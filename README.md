作成中
## AI関連の処理を行うPythonライブラリ



## APIの説明

### request
この説明はJSONC形式(コメント付きJOSN)で記載していますが、実際のリクエストはJSON形式で記述してください。
```jsonc
{
    // -----------------------------------------------------------
    // 基本設定
    // -----------------------------------------------------------
    // openaiを使用する場合の基本設定用ディクショナリ 
    "openai_props": {
        // str: OpenAIのAPIキー
        "OpenAIKey": "" ,
        // bool: Azure OpenAIを使用するか否か
        "AzureOpenAI": false,
        // str: AureOpenAIのAPIバージョン AuzreOpenAI=trueの場合に設定する。
        "AzureOpenAIAPIVersion": "",
        // str: AureOpenAIのエンドポイントURL AuzreOpenAI=trueの場合に設定する。
        "AzureOpenAIEndpoint": "",
        // str: カスタムモデル用のBaseURL OpenAI,AzureOpenAI以外のカスタムモデルを使用する場合に設定する。
        "OpenAIBaseURL": ""
    },
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
    "chat_request": {
        // チャットに使用するモデル
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
    // マージチャット(複数のドキュメントに同一のプロンプトを与えた結果をマージ)やサイズの大きいドキュメントを分割する場合の
    // chat_requestの補助的なディクショナリ。
    "chat_request_context": {
        "prompt_template_text": "",
        "chat_mode": "Normal",
        "split_mode": "None",
        "summarize_prompt_text": "単純に結合しただけなので、文章のつながりがよくない箇所があるかもしれません。 文章のつながりがよくなるように整形してください。 出力言語は日本語にしてください。\n",
        "related_information_prompt_text": "------ 以下は本文に関連する情報をベクトルDBから検索した結果です。---\n",
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
      {  "Id" : "タグID",
        "Tag" : "タグ名",
        "IsPinned" : "ピン留め状態"
        }
    ]

}
```

### response



