作成中
## AI関連の処理を行うPythonライブラリ

## 機能
* OpenAIまたはAzureOpenAIを使用したチャット機能
  * 生成AIを使用した通常のチャット
  * 大きなサイズの文章を分割してプロンプトで指示を与えた結果をマージ、マージをサマライズする機能
  * ベクトルDB(chroma + sqlite3)に格納したデータを用いたRAG機能
* ベクトル検索機能
  ベクトルDBに格納されたデータのベクトル検索
* ベクトル登録機能
  文章をベクトル化してベクトルDBに格納する。

## APIサーバー

## コマンドラインツール(APIクライアント版)
### 生成AIチャット
```
Usage: python normal_chat_api.py -f <request_json_file> [-s <api_base>] [-i] [-m <message>]
Options:
  -f <request_json_file> : リクエストJSONファイル
  -s <api_base>          : APIのURL
  -i                     : インタラクティブモード
  -m <message>           : メッセージ
  -h                     : ヘルプ
```
### ベクトル検索
```
Usage: python vector_search_api.py  -s <api_base> [-f <request_json_file>] [-k <search_result_count>] [-p <vector_db_folder>] [-m <message>]
Options:
  -f <request_json_file>   : リクエストJSONファイル
  -s <api_base>            : APIのURL
  -p <vector_db_folder>    : ベクトルDBの検索対象フォルダ
  -k <search_result_count> : 検索結果の数
  -m <message>             : メッセージ
  -h                       : ヘルプ
```

## コマンドラインツール(ローカル実行版)
### 生成AIチャット
```
Usage: python normal_chat_local.py -f <request_json_file> [-d <app_data_path>] [-i] [-m <message>]
Options:
  -f <request_json_file> : リクエストJSONファイル
  -d <app_data_path>     : アプリケーションデータのパス
  -i                     : インタラクティブモード
  -m <message>           : メッセージ
  init                   : アプリケーション環境の初期設定を実施
  -h                     : ヘルプ
```

## APIの説明

### request
この説明はJSONC形式(コメント付きJOSN)で記載していますが、実際のリクエストはコメントを除去して、JSON形式で記述してください。
```jsonc
{
    // -----------------------------------------------------------
    // 基本設定
    // -----------------------------------------------------------
    // autogenを使用する場合の基本設定用ディクショナリ AutoGenを使用しない場合には不要
    "autogen_props": {
        // str: autogenの作業用ディレクトリ
        "work_dir": "",
        // str: ツール出力ディレクトリ
        "tool_dir": "",
        // str: チャット履歴フォルダのフォルダID
        "chat_history_folder_id": "",
        // AutoGenのチャットタイプ： group,normalのいずれか。groupの場合はグループチャット、normalの場合はAgentチャット
        "chat_type": "group",
        // AutoGenのチャット設定名
        "chat_name": "default",
        // チャット終了条件の文字列
        "terminate_msg": "TERMINATE",
        // チャット終了条件のメッセージ数 
        "max_msg": 15,
        // チャット終了条件のタイムアウト時間
        "timeout": 120,
        // str: セッションキャンセル用のトークン。UUIDなどの一意の値を指定する
        "session_token": ""
    },

    // -----------------------------------------------------------
    // リクエスト毎のディクショナリ
    // -----------------------------------------------------------
    // OpenAIチャット、AutoGenチャットで使用するリクエスト用のディクショナリ。
    // フォーマットは https://platform.openai.com/docs/guides/text?api-mode=chat を参照
    "chat_request": {
        "model": "gpt-4o-mini",
        "messages": [
        {
            "role": "user", 
            "content": [
            {
                "type": "text",
                "text": "\n\n"
            }
            ]
        }
        ],
        "temperature": 0.5
    },
    // chat_requestの補助的なディクショナリ。
    // マージチャット(複数のドキュメントに同一のプロンプトを与えた結果をマージ)やサイズの大きいドキュメントを分割する場合などに使用.
    "chat_request_context": {
        "chat_mode": "Normal",
        // 分割処理を行うかどうか。
        // * None:   
        //   何もしない。 入力のサイズが最大トークン数を超えた場合はエラーとなる。
        // * NormalSplit:  
        //   指定したトークンサイズで入力を分割して処理を行い、最後にマージする。
        //   分割した入力にはprompt_template_textで指定したプロンプトが適用される。
        // * SplitAndSummarize: 
        //   NormalSplit分割&マージした後、サマリーの生成を行う。サマリー生成にはsummarize_prompt_textで指定したプロンプトが適用される。
        "split_mode": "None",
        "prompt_template_text": "",
        "summarize_prompt_text": "",
        // RAGを有効にするかどうか。
        // * None:  
        //   RAGを使用しない。
        // * NormalSearch:  
        //   入力を元にベクトル検索を実行。チャット内で関連情報として使用。
        // * PrompSearch
        //   rag_prompt_textで指示した内容を入力に適用した結果を元にベクトル検索を行う。
        "rag_mode": "None",
        "rag_mode_prompt_text": "",
    },
    // ベクトル検索を行う場合のディクショナリ。ベクトル検索APIを実行する場合に使用する。
    "vector_search_requests": [
    {
        "name": "default",
        "model": "str: embeddingに使用するモデル. 例：text-embedding-3-small",
        "query": "str: 検索文字列",
        "search_kwargs": {
            "k": "int: ベクトル検索結果の数",
            "score_threshold": "コサイン類似度の閾値",
            "filter": {
                "folder_id": "検索対象のフォルダのID. folder_id、folder_pathが指定されていない場合はDB内を全検索",
                "folder_path" : "フォルダのパス.指定されている場合はfolder_idよりも優先される"
            }
        }
    }
    ],
    // ベクトル生成を行う場合のディクショナリ。ベクトル生成APIを実行する場合に使用する。
    "embedding_request":
        {
        "name": "default",
        "model": "text-embedding-3-small",
        "doc_id": "",
        "folder_id": "フォルダID",
        "folder_path": "フォルダパス",
        "source_id": "",
        "source_path": "",
        "source_type": 0,
        "description": "",
        "content": "",
    },
    // -----------------------------------------------------------
    // 設定編集用のディクショナリ
    // -----------------------------------------------------------
    // ベクトルDBの参照、編集のためのディクショナリ。
    "vector_db_item_request" : {
        "id": "ベクトルDBのID",
        "name": "ベクトルDBの名前",
        "description": "ベクトルDBの説明",
        "vector_db_url": "ベクトルDBのURLまたはパス",
        "is_use_multi_vector_retriever": "MultiVectorRetrieverを使用するかどうか",
        "doc_store_url": "MultiVectorRetriever用のDBのURL",
        "vector_db_type": "0:Chroma, 1:PGVector",
        "collection_name": "ベクトル格納用のコレクション名",
        "chunk_size": "チャンクサイズ。データはこの単位に分割してベクトル化する",
        "default_search_result_limit": "デフォルトの検索結果表示数",
        "is_enabled": "このベクトルDBを有効にするか否か。",
        "is_system": "システム用のベクトルDBか否か"
    },
    // フォルダ
    "content_folder_requests": {
        "id" : "フォルダのID",
        "folder_name" : "フォルダ名",
        "folder_type_string": "フォルダの種別",
        "description": "フォルダの説明",
        // ルートフォルダか否か
        "is_root_folder": false,
        "extended_properties_json" : "",
        "parent_id": "",
        "folder_path": ""
    },

    // AutoGenのLLM設定の参照、編集のためのディクショナリ。
    "autogen_llm_config_request": {
        "name": "名前",
        "api_type" : "APIのタイプ",
        "api_version" : "APIバージョン",
        "model" : "モデル",
        "api_key" : "APIキー",
        "base_url" : "BaseURL"
    },

    // AutoGenのTool設定の参照、編集のためのディクショナリ。
    "autogen_tool_request": {
        "name": "名前",
        "path": "パス",
        "description": "説明"
    },

    // AutoGenのAgent設定の参照、編集のためのディクショナリ。
    "autogen_agent_request": {
        "name": "名前",
        "description": "説明",
        "system_message": "システムメッセージ",
        "code_execution" : "コード実行",
        "llm_config_name" : "LLMの設定",
        "tool_names" : "ツール名",
        "vector_db_props" : "vector_db_props"
    },

    // AutoGenのグループチャット設定の参照、編集のためのディクショナリ。
    "autogen_group_chat_request": {
        "name": "名前",
        "description": "説明",
        "llm_config_name": "LLMの設定",
        "agent_names": "AIエージェント"
    },

    // 共有タグの参照、編集のためのディクショナリ。現在は未使用
    "tag_item_requests" : [
      {  "id" : "タグID",
        "tag" : "タグ名",
        "is_pinned" : "ピン留め状態"
        }
    ]

}
```

### response



