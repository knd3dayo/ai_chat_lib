import json
from typing import Any, Callable, Union
import copy
import time
import tiktoken
from openai import  RateLimitError

from ai_chat_lib.llm_modules import OpenAIClient, OpenAIProps
from ai_chat_lib.langchain_modules import  LangChainUtil
from ai_chat_lib.db_modules import VectorSearchRequest

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

# リクエストコンテキスト
class RequestContext:

    chat_request_context_name = "chat_request_context"
    @classmethod
    def get_chat_request_context_objects(cls, request_dict: dict) -> "RequestContext":
        '''
        {"chat_request_context": {}}の形式で渡される
        '''
        # chat_request_contextを取得
        chat_request_context_dict = request_dict.get(cls.chat_request_context_name, None)
        if not chat_request_context_dict:
            raise ValueError("request_context is not set.")

        result = RequestContext(chat_request_context_dict)
        return result

    chat_mode_name = "chat_mode" 
    prompt_template_text_name = "prompt_template_text"
    summarize_prompt_text_name = "summarize_prompt_text"
    related_information_prompt_text_name = "related_information_prompt_text"

    # split_mode
    split_mode_name = "split_mode"
    split_mode_name_split_and_summarize = "SplitAndSummarize"
    split_mode_name_none = "None"
    split_mode_name_normal = "NormalSplit"

    split_token_count_name = "split_token_count"

    # rag_mode
    rag_mode_name = "rag_mode"
    rag_mode_name_none = "None"
    rag_mode_name_normal_search = "NormalSearch"
    rag_mode_name_prompt_search = "PromptSearch"
    rag_mode_prompt_text_name = "rag_mode_prompt_text"


    def __init__(self, request_context_dict: dict):
        self.PromptTemplateText = request_context_dict.get(RequestContext.prompt_template_text_name, "")
        self.ChatMode = request_context_dict.get(RequestContext.chat_mode_name, "Normal")
        self.SplitMode = request_context_dict.get(RequestContext.split_mode_name, "None")
        self.SplitTokenCount = request_context_dict.get(RequestContext.split_token_count_name, 8000)
        self.SummarizePromptText = request_context_dict.get(RequestContext.summarize_prompt_text_name, "")

        self.RAGMode = request_context_dict.get(RequestContext.rag_mode_name, RequestContext.rag_mode_name_none)
        self.RAGModePrompt = request_context_dict.get(RequestContext.rag_mode_prompt_text_name, "")

        self.RelatedInformationPromptText = "Below are the results retrieved from the vector database related to the main content.\n---\n"


class ChatUtil:

    chat_request_name = "chat_request"
    @classmethod
    async def run_openai_chat_async_api(cls, request_dict: dict) -> dict:

        openai_props = OpenAIProps.create_from_env()
        # context_jsonからVectorSearchRequestを生成
        vector_search_requests = await VectorSearchRequest.get_vector_search_requests_objects(request_dict)
        # context_jsonからChatRequestContextを生成
        chat_request_context = RequestContext.get_chat_request_context_objects(request_dict)
        # chat_requestを取得
        chat_request_dict = request_dict.get(cls.chat_request_name, None)
        if not chat_request_dict:
            raise ValueError("chat_request is not set")

        return await cls.run_openai_chat_async(openai_props, chat_request_context, chat_request_dict, vector_search_requests)

    token_count_request_name = "token_count_request"
    @classmethod
    def get_token_count_api(cls, request_json: str):
        # request_jsonからrequestを作成
        request_dict: dict = json.loads(request_json)

        # input_textを取得
        token_count_request = request_dict.get(cls.token_count_request_name, None)
        if not token_count_request:
            raise ValueError("token_count_request is not set")
        model = token_count_request.get("model", None)
        if not model:
            raise ValueError("model is not set")
        input_text = token_count_request.get("input_text", "")
        if not input_text:
            raise ValueError("input_text is not set")
        result: dict = {}
        result["total_tokens"] = ChatUtil.get_token_count(model, input_text)
        return result

    chat_contatenate_request_name = "chat_contatenate_request"

    @classmethod
    def get_token_count_objects(cls, request_dict: dict) -> dict:
        '''
        {"context": {"token_count_request": {}}}の形式で渡される
        '''

        # token_count_request_nameを取得
        token_count_request = request_dict.get(cls.token_count_request_name, None)
        if not token_count_request:
            raise ValueError("token_count_request is not set")
        return token_count_request


    @classmethod
    def split_message(cls, message_list: list[str], model: str, split_token_count: int) -> list[str]:
        # token_countが80KBを超える場合は分割する
        result_message_list = []
        temp_message_list: list[str] = []
        total_token_count = 0
        for i in range(0, len(message_list)):
            message = message_list[i] + "\n"
            token_count = cls.get_token_count(model, message)
            # total_token_count + token_countが80KBを超える場合はtemp_message_listをresult_message_listに追加する
            if total_token_count + token_count > split_token_count:
                result_message_list.append("\n".join(temp_message_list))
                temp_message_list = []
                total_token_count = 0
            temp_message_list.append(message)
            total_token_count += token_count
        # temp_message_listが空でない場合はresult_message_listに追加する
        if len(temp_message_list) > 0:
            result_message_list.append("\n".join(temp_message_list))
        # result_message_listを返す
        return result_message_list


    @classmethod
    def __get_last_message_dict(cls, input_dict: dict) -> dict:
        '''
        input_dictのmessagesのtext要素を取得する
        '''
        return input_dict["messages"][-1]

    @classmethod
    def __get_last_message(cls, message_dict: dict) -> tuple[int, str]:
        '''
        message_dictのmessagesの最後のtext要素を取得する
    
        '''
        # "messages"のtext要素を取得する       
        text_content_index = -1
        for i in range(0, len(message_dict["content"])):
            if message_dict["content"][i]["type"] == "text":
                text_content_index = i
                break
        # last_text_content_indexが-1の場合はエラーをraiseする
        if text_content_index == -1:
            raise ValueError("last_text_content_index is -1")
        # queryとして最後のtextを取得する
        last_message = message_dict["content"][text_content_index]["text"]
        return text_content_index, last_message


    @classmethod
    def __exec_vector_search(cls, vector_search_function: Callable, query: str) -> tuple[str, dict[str, dict]]:  
        # ベクトル検索結果のdocumentを格納するdictを作成する
        result_documents_dict: dict[str, dict] = {}
        vector_search_result = vector_search_function(query) 
        # vector_search_resultのcontentを取得する
        vector_search_result_contents_text = "\n".join([ document["content"] for document in vector_search_result["documents"]])

        # 参考ドキュメント一覧用のdocument一覧の作成。source_idが重複しているdocumentを排除する。
        for document in vector_search_result["documents"]:
            logger.info(document)
            result_documents_dict[document["doc_id"]] = document

        return vector_search_result_contents_text, result_documents_dict

    @classmethod
    def __pre_process_input(
            cls, client: OpenAIClient, model: str, request_context:RequestContext, last_message_dict: dict, 
            vector_search_function : Union[Callable, None]) -> tuple[list[dict], list[dict]]:

        # "messages"の最後のtext要素を取得する       
        last_text_content_index, original_last_message = cls.__get_last_message(last_message_dict)

        # request_contextのSplitModeがNone以外の場合はoriginal_last_messageを改行毎にtokenをカウントして、
        # 80KBを超える場合は分割する
        # 結果はresult_messagesに格納する

        result_messages = []
        result_documents_dict = {}  # Ensure this is always defined
        # SplitoModeの処理 SplitModeがNone以外の場合は分割する
        if request_context.SplitMode != RequestContext.split_mode_name_none:
            splited_messages = cls.split_message(original_last_message.split("\n"), model, request_context.SplitTokenCount)
        else:
            splited_messages = [original_last_message]

        for i in range(0, len(splited_messages)):
            # 分割したメッセージを取得する毎に、プロンプトテンプレートと関連情報を取得する
            target_message = splited_messages[i]
            # context_message 
            context_message = ""
            if i > 0 and len(request_context.PromptTemplateText) > 0:
                context_message = request_context.PromptTemplateText + "\n\n"

            # RAGモードの処理
            # None以外の場合はvector_search_functionが設定されているので、ベクトル検索を実行する
            if vector_search_function:
                # ベクトル検索用の文字列としてqueryにtarget_messageを設定する
                query = target_message
                vector_search_result_contents_text, result_documents_dict = cls.__exec_vector_search(vector_search_function, query)
                # ベクトル検索結果をcontext_messageに追加する
                context_message += request_context.RelatedInformationPromptText + vector_search_result_contents_text

            # last_messageをdeepcopyする
            result_last_message = copy.deepcopy(last_message_dict)
            # result_last_messageのcontentの最後の要素を更新する
            result_last_message["content"][last_text_content_index]["text"] = f"{context_message}\n{target_message}"
            # result_messagesに追加する
            result_messages.append(result_last_message)

        return result_messages, [ value for value in result_documents_dict.values()]

    @classmethod
    async def __post_process_output_async(cls, client: OpenAIClient, request_context: RequestContext, 
                            input_dict: dict, chat_result_dict_list: list[dict],
                            docs_list: list[dict]) -> dict:

        # RequestContextのSplitModeがNormalSplitの場合はchat_result_dict_listのoutputを結合した文字列とtotal_tokensを集計した結果を返す
        if request_context.SplitMode == RequestContext.split_mode_name_normal:
            output = "\n".join([chat_result_dict["output"] for chat_result_dict in chat_result_dict_list])
            total_tokens = sum([chat_result_dict["total_tokens"] for chat_result_dict in chat_result_dict_list])
            return {"output": output, "total_tokens": total_tokens, 
                    "documents": docs_list
                    }
        
        # RequestContextのSplitModeがSplitAndSummarizeの場合はSummarize用のoutputを作成する
        if request_context.SplitMode == RequestContext.split_mode_name_split_and_summarize:
            summary_prompt_text = ""
            if len(request_context.PromptTemplateText) > 0:
                summary_prompt_text = f"""
                The following text is a document that was split into several parts, and based on the instructions of [{request_context.PromptTemplateText}], 
                the AI-generated responses were combined. 
                {request_context.PromptTemplateText}
                """

            else:
                summary_prompt_text = """
                The following text is a document that has been divided into several parts, with AI-generated responses combined.
                {request_context.PromptTemplateText}
                """
            summary_input =  summary_prompt_text + "\n".join([chat_result_dict["output"] for chat_result_dict in chat_result_dict_list])
            total_tokens = sum([chat_result_dict["total_tokens"] for chat_result_dict in chat_result_dict_list])
            # openai_chatの入力用のdictを作成する
            summary_input_dict = OpenAIProps.create_openai_chat_parameter_dict_simple(input_dict["model"], summary_input, input_dict.get("temperature", 0.5), input_dict.get("json_mode", False))
            # chatを実行する
            summary_result_dict = await cls.call_openai_completion_async(client, summary_input_dict)
            # total_tokensを更新する
            summary_result_dict["total_tokens"] = total_tokens + summary_result_dict["total_tokens"]
            summary_result_dict["documents"] = docs_list
            return summary_result_dict
        
        # RequestContextのSplitModeがNoneの場合はoutput_dictの1つ目の要素を返す
        result_dict = chat_result_dict_list[0]
        result_dict["documents"] = docs_list
        return result_dict 
    
    @classmethod
    async def run_openai_chat_async(cls, openai_props: OpenAIProps, request_context: RequestContext ,input_dict: dict, vector_search_requests : list[VectorSearchRequest]) -> dict:
        # ★TODO 分割モードの場合とそうでない場合で処理を分ける
        # 分割モードの場合はそれまでのチャット履歴をどうするか？
        
        # pre_process_inputを実行する
        last_message_dict = cls.__get_last_message_dict(input_dict)
        # modelを取得する
        model = input_dict.get("model", None)
        if not model:
            raise ValueError("model is not set")
        
        # 最後のメッセージの分割処理、ベクトル検索処理を行う
        # OpenAIClientを取得する
        client = OpenAIClient(openai_props)

        # ベクトル検索関数
        async def vector_search(query: str) -> dict:
            # vector_db_itemsの各要素にqueryを設定
            for vector_search_request in vector_search_requests:
                vector_search_request.query = query
            return await LangChainUtil.vector_search(openai_props, vector_search_requests)

        # vector_db_itemsが空の場合はNoneを設定
        vector_search_function: Union[Callable, None] = None if request_context.RAGMode == RequestContext.rag_mode_name_none or (vector_search_requests) == 0 else vector_search

        pre_processed_input_list, docs_list = cls.__pre_process_input(client, model, request_context, last_message_dict, vector_search_function)
        chat_result_dict_list = []

        for pre_processed_input in pre_processed_input_list:
            # input_dictのmessagesの最後の要素のみを取得する
            copied_input_dict = copy.deepcopy(input_dict)

            # split_modeがNone以外の場合はinput_dictのmessagesの最後の要素のみを取得する
            # ★TODO split_modeの場合は履歴を無視している。LRU的な仕組みを入れる
            if request_context.SplitMode != "None":
                copied_input_dict["messages"] = [pre_processed_input]
            else:
                copied_input_dict["messages"][-1] = pre_processed_input

            chat_result_dict = await cls.call_openai_completion_async(client, copied_input_dict)
            # chat_result_dictをchat_result_dict_listに追加する
            chat_result_dict_list.append(chat_result_dict)

        # post_process_outputを実行する
        result_dict = await cls.__post_process_output_async(client, request_context, input_dict, chat_result_dict_list, docs_list)
        return result_dict
    
    @classmethod
    async def call_openai_completion_async(cls, client: OpenAIClient, input_dict: dict) -> dict:
        # openai.
        # RateLimitErrorが発生した場合はリトライする
        # リトライ回数は最大で3回
        # リトライ間隔はcount*30秒
        # リトライ回数が5回を超えた場合はRateLimitErrorをraiseする
        # リトライ回数が5回以内で成功した場合は結果を返す
        # OpenAIのchatを実行する
        completion_client = client.get_completion_client()
        count = 0
        response = None
        while count < 3:
            try:
                response = await completion_client.chat.completions.create(
                    **input_dict
                )
                break
            except RateLimitError as e:
                count += 1
                # rate limit errorが発生した場合はリトライする旨を表示。英語
                logger.warn(f"RateLimitError has occurred. Retry after {count*30} seconds.")
                time.sleep(count*30)
                if count == 5:
                    raise e
        if response is None:
            raise RuntimeError("Failed to get a response from OpenAI after retries.")
        # token情報を取得する
        total_tokens = response.usage.total_tokens
        # contentを取得する
        content = response.choices[0].message.content

        # dictにして返す
        logger.info(f"chat output:{json.dumps(content, ensure_ascii=False, indent=2)}")
        return {"output": content, "total_tokens": total_tokens}

    @classmethod
    def get_token_count(cls, model: str, input_text: str) -> int:
        # completion_modelに対応するencoderを取得する
        encoder = tiktoken.encoding_for_model(model)
        # token数を取得する
        return len(encoder.encode(input_text))
   

