import json
from typing import ClassVar
from pydantic import BaseModel, Field
import copy
import tiktoken

from ai_chat_lib.chat_modules.llm.openai_util import OpenAIClient, OpenAIProps, CompletionRequest, CompletionOutput, MessageItem
from ai_chat_lib.chat_modules.langchain.langchain_util import  LangChainUtil
from ai_chat_lib.chat_modules.langchain.vector_search_request import VectorSearchRequest

import ai_chat_lib.log_modules.log_settings as log_settings
logger = log_settings.getLogger(__name__)

class ChatRequestContext(BaseModel):


    # split_mode
    split_mode_name_none: ClassVar[str] = "None"
    split_mode_name_normal: ClassVar[str] = "NormalSplit"
    split_mode_name_split_and_summarize: ClassVar[str] = "SplitAndSummarize"

    # rag_mode
    rag_mode_name_none: ClassVar[str] = "None"
    rag_mode_name_normal_search: ClassVar[str] = "NormalSearch"
    rag_mode_name_prompt_search: ClassVar[str] = "PromptSearch"

    chat_mode: str = Field(default="Normal")
    split_mode: str = Field(default="None")
    split_token_count: int = Field(default=8000)
    max_images_per_request: int = Field(default=4)
    summarize_prompt_text: str = Field(default="")
    prompt_template_text: str = Field(default="")
    rag_mode: str = Field(default=rag_mode_name_none)
    rag_mode_prompt: str = Field(default="")
    related_information_prompt_text: str = Field(
        default="Below are the results retrieved from the vector database related to the main content.\n---\n"
    )

class ChatUtil:

    @classmethod
    def split_message(cls, original_message: list[str], model: str, split_token_count: int) -> list[str]:
        # token_countがsplit_token_countを超える場合は分割する
        result_message_list = []
        current_message = ""
        for line in original_message:
            line_token_count = cls.get_token_count(model, line)
            current_message_token_count = cls.get_token_count(model, current_message)
            if current_message_token_count + line_token_count > split_token_count:
                # current_messageをresult_message_listに追加する
                result_message_list.append(current_message)
                # current_messageを初期化する
                current_message = line + "\n"
            else:
                current_message += line + "\n"
        # 最後のcurrent_messageをresult_message_listに追加する
        if len(current_message) > 0:
            result_message_list.append(current_message)

        return result_message_list

    @classmethod
    def __get_last_message_image_urls(cls, message_dict: MessageItem) -> tuple[int, list[str]]:
        '''
        message_dictのmessagesの最後のimage_url要素を取得する
    
        '''
        image_urls = []
        message_index = -1
        # "messages"のimage_url要素を取得する
        for i in range(0, len(message_dict.content)):
            if message_dict.content[i]["type"] == "image_url":
                image_urls.append(message_dict.content[i]["image_url"]["url"])
                message_index = i

        return message_index, image_urls

    @classmethod
    def __get_last_message_text(cls, message_dict: MessageItem) -> tuple[int, str]:
        '''
        message_dictのmessagesの最後のtext要素を取得する
    
        '''
        message_index = -1
        # "messages"のtext要素を取得する       
        for i in range(0, len(message_dict.content)):
            if message_dict.content[i]["type"] == "text":
                message_index = i
                break
        # message_indexが-1の場合はエラーをraiseする
        if message_index == -1:
            raise ValueError("last_text_content_index is -1")
        # queryとして最後のtextを取得する
        last_message = message_dict.content[message_index]["text"]
        return message_index, last_message

    @classmethod
    async def __pre_process_input(
            cls, client: OpenAIClient, model: str, request_context: ChatRequestContext, original_chat_request: CompletionRequest,
            vector_search_requests: list[VectorSearchRequest]) -> tuple[list[CompletionRequest], list[dict]]:
        '''
        メッセージ分割、ベクトル検索を実行する
        split_modeがNoneの場合はメッセージ分割を実行しない。
        split_modeがNone以外の場合はメッセージ分割を実行する。また、image_urlも分割する
        その後、rag_modeがNone以外の場合はベクトル検索を実行する
        返り値は、分割後のChatRequestのリストとベクトル検索結果のリスト
        '''


        # 結果格納用のChatRequestのリストを作成する
        result_chat_request_list: list[CompletionRequest] = []

        # pre_process_inputを実行する
        chat_request = copy.deepcopy(original_chat_request)
        # chat_requestのmessagesの最後の要素を取得する
        last_message_dict = chat_request.messages.pop()
        if not last_message_dict:
            raise ValueError("No last message found in input_dict")


        # "messages"の最後のtext要素を取得する       
        last_text_content_index, original_last_message = cls.__get_last_message_text(last_message_dict)

        # "messages"の最後のimage_url要素を取得する       
        last_images_content_index, image_urls = cls.__get_last_message_image_urls(last_message_dict)

        # request_contextのSplitModeがNone以外の場合はoriginal_last_messageを改行毎にtokenをカウントして、
        # split_token_countを超える場合は分割する

        result_documents_dict = {}  # Ensure this is always defined
        vector_search_result_message = ""

        # rag_modeの処理 rag_modeがNone以外の場合はベクトル検索を実行する
        if len(vector_search_requests) > 0 and request_context.rag_mode != ChatRequestContext.rag_mode_name_none:
            # ベクトル検索用の文字列としてqueryにtarget_messageを設定する
            for vector_search_request in vector_search_requests:
                vector_search_request.query = original_last_message

            result_documents = await LangChainUtil.vector_search(client.props, vector_search_requests)
            texts = [doc.page_content for doc in result_documents]  
            # ベクトル検索結果のメッセージを作成する
            vector_search_result_message = request_context.related_information_prompt_text + "\n".join(texts) + "\n\n"

        # split_modeがNoneの場合は、context_message, original_last_message, vector_search_result_messageを結合して
        # chat_requestのmessagesに追加する
        if request_context.split_mode == ChatRequestContext.split_mode_name_none:
            chat_request.add_text_message(CompletionRequest.user_role_name, 
                f"{request_context.prompt_template_text}\n{original_last_message}\n\n{vector_search_result_message}")
            # image_urlが存在する場合はchat_requestに追加する
            for image_url in image_urls:
                chat_request.append_image_to_last_message(CompletionRequest.user_role_name, image_url)

            # result_chat_request_listにchat_requestを追加する
            result_chat_request_list.append(chat_request)
            return result_chat_request_list, [ value for value in result_documents_dict.values()]

        # SplitModeがNone以外の場合はoriginal_last_messageを分割する
        splited_messages = cls.split_message(original_last_message.split("\n"), model, request_context.split_token_count)
        for i in range(0, len(splited_messages)):
            # 分割したメッセージを取得する毎に、プロンプトテンプレートと関連情報を取得する
            target_message = splited_messages[i]
            # chat_requestをdeepcopyする
            result_chat_request = copy.deepcopy(chat_request)
            
            # result_chat_requestのmessagesにtext_messageを追加する
            result_chat_request.add_text_message(CompletionRequest.user_role_name, 
                f"{request_context.prompt_template_text}\n{target_message}\n\n{vector_search_result_message}")
            # result_chat_request_listにresult_chat_requestを追加する
            result_chat_request_list.append(result_chat_request)

        # SplitModeがNone以外の場合はimage_urlsを分割する。
        splited_image_urls = []
        if request_context.split_mode != ChatRequestContext.split_mode_name_none:
            max_images_per_request = request_context.max_images_per_request
            if len(image_urls) > 0 and max_images_per_request > 0:
                for i in range(0, len(image_urls), max_images_per_request):
                    splited_image_urls.append(image_urls[i:i + max_images_per_request])
        else:
            splited_image_urls = [image_urls]
        
        # splited_image_urls毎にchat_requestを作成してresult_chat_request_listに追加する
        for i in range(0, len(splited_image_urls)):
            image_urls = splited_image_urls[i]
            if len(image_urls) == 0:
                continue
            # chat_requestをdeepcopyする
            result_chat_request = copy.deepcopy(chat_request)
            # image_urlsをresult_chat_requestに追加する
            for image_url in image_urls:
                message = f"{request_context.prompt_template_text}\n\n{vector_search_result_message}"
                result_chat_request.add_image_message(CompletionRequest.user_role_name, message, image_url)
            # result_chat_request_listにresult_chat_requestを追加する
            result_chat_request_list.append(result_chat_request)
        return result_chat_request_list, [ value for value in result_documents_dict.values()]

    @classmethod
    async def __post_process_output_async(cls, client: OpenAIClient, request_context: ChatRequestContext, 
                            input_dict: CompletionRequest, chat_output_list: list[CompletionOutput],
                            docs_list: list[dict]) -> CompletionOutput:

        # RequestContextのSplitModeがNormalSplitの場合はchat_result_dict_listのoutputを結合した文字列とtotal_tokensを集計した結果を返す
        if request_context.split_mode == ChatRequestContext.split_mode_name_normal:
            output = ""
            total_tokens = 0
            for i in range(0, len(chat_output_list)):
                logger.debug(f"chat_output_list[{i}]: {chat_output_list[i]}")
                output += f"output:[{i}]\n {chat_output_list[i].output}\n"
                total_tokens += chat_output_list[i].total_tokens

            return CompletionOutput(output=output, total_tokens=total_tokens, documents=docs_list)

        # RequestContextのSplitModeがSplitAndSummarizeの場合はSummarize用のoutputを作成する
        if request_context.split_mode == ChatRequestContext.split_mode_name_split_and_summarize:
            summary_prompt_text = ""
            if len(request_context.prompt_template_text) > 0:
                summary_prompt_text = f"""
                The following text is a document that was split into several parts, and based on the instructions of [{request_context.prompt_template_text}], 
                the AI-generated responses were combined. 
                {request_context.prompt_template_text}
                """
            else:
                summary_prompt_text = """
                The following text is a document that has been divided into several parts, with AI-generated responses combined.
                {request_context.PromptTemplateText}
                """
            
            summary_input =  summary_prompt_text + "\n".join([chat_output.output for chat_output in chat_output_list])
            total_tokens = sum([chat_output.total_tokens for chat_output in chat_output_list])
            # openai_chatの入力用のdictを作成する
            summary_input_dict = OpenAIProps.create_openai_chat_parameter_dict_simple(input_dict.model, summary_input, input_dict.temperature,  False)
            summary_chat_request = CompletionRequest(**summary_input_dict)
            # chatを実行する
            summary_chat_output = await client.run_completion_async(summary_chat_request)
            # total_tokensを更新する
            summary_chat_output.total_tokens = total_tokens + summary_chat_output.total_tokens
            summary_chat_output.documents = docs_list
            return summary_chat_output
        else:
            # RequestContextのSplitModeがNoneの場合はoutput_dictの1つ目の要素を返す
            chat_output = chat_output_list[0]
            chat_output.documents = docs_list
            return chat_output

    @classmethod
    async def run_openai_chat_async(cls, openai_props: OpenAIProps, request_context: ChatRequestContext ,input_dict: CompletionRequest, vector_search_requests : list[VectorSearchRequest]) -> CompletionOutput:
        # ★TODO 分割モードの場合とそうでない場合で処理を分ける
        # 分割モードの場合はそれまでのチャット履歴をどうするか？
        
        # modelを取得する
        model = input_dict.model
        if not model:
            raise ValueError("model is not set")
        
        # 最後のメッセージの分割処理、ベクトル検索処理を行う
        # OpenAIClientを取得する
        client = OpenAIClient(openai_props)

        pre_processed_chat_request_list, docs_list = await cls.__pre_process_input(
            client, model, request_context, input_dict, vector_search_requests
            )
        chat_result_dict_list = []

        for pre_processed_chat_request in  pre_processed_chat_request_list:

            chat_result_dict = await client.run_completion_async(pre_processed_chat_request)
            # chat_result_dictをchat_result_dict_listに追加する
            chat_result_dict_list.append(chat_result_dict)

            # 0.5秒待機する
            import time
            time.sleep(0.5)

        # post_process_outputを実行する
        result_dict = await cls.__post_process_output_async(
            client, request_context, input_dict, chat_result_dict_list, docs_list
        )
        return result_dict
    

    @classmethod
    def get_token_count(cls, model: str, input_text: str) -> int:
        # completion_modelに対応するencoderを取得する
        # 暫定処理 
        # "gpt-4.1-": "o200k_base",  # e.g., gpt-4.1-nano, gpt-4.1-mini
        # "gpt-4.5-": "o200k_base", # e.g., gpt-4.5-preview
        if model.startswith("gpt-41") or model.startswith("gpt-4.1") or model.startswith("gpt-4.5"):
            encoder = tiktoken.get_encoding("o200k_base")
        else:
            encoder = tiktoken.encoding_for_model(model)
        # token数を取得する
        return len(encoder.encode(input_text))
   

