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
    // 検索ルール
    "search_rule_requests": [{
      "id": "検索ルールID",
      "search_condition_json": "{検索条件}",
      "is_include_sub_folder": false,
      "is_global_search": true
    }],
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
    "content_folder_requests": [{
        "id" : "フォルダのID",
        "folder_name" : "フォルダ名",
        "folder_type_string": "フォルダの種別",
        "description": "フォルダの説明",
        // ルートフォルダか否か
        "is_root_folder": false,
        "extended_properties_json" : "",
        "parent_id": "",
        "folder_path": ""
    }],
    // アイテム
    "content_item_requests": [ {    
        "id" : "",
        "folder_id" : "",
        "created_at" : "",
        "updated_at" : "",
        "vectorized_at": "",
        "content" : "",
        "description" : "",
        "content_type" : "",
        "chat_messages_json" : "",
        "prompt_chat_result_json" : "",
        "tag_string" : "",
        "is_pinned" : "",
        "cached_base64_string" : "",
        "extended_properties_json" ""
    }],

    // 共有タグの参照、編集のためのディクショナリ。現在は未使用
    "tag_item_requests" : [
      {  "id" : "タグID",
        "tag" : "タグ名",
        "is_pinned" : "ピン留め状態"
        }
    ],
    // AutoProcessItem
    "auto_process_item_requests": [{
        "id": "自動処理ルールアイテムのID",
        "display_name": "自動処理ルールアイテムの表示名",
        "description": "自動処理ルールアイテムの説明",
        "auto_process_item_type": "自動処理ルールアイテムのタイプ", 
        "action_type": "自動処理ルールアイテムのアクションタイプ",
    }],
    // AutoProcessRule
    "auto_process_rule_requests": [{
        "id": "自動処理ルールのID",
        "rule_name": "自動処理ルールの名前",
        "is_enabled": true, //"自動処理ルールの説明"
        "priority": -1, 
        "conditions_json": "{}",
        "auto_process_item_id": "自動処理アイテムのID",
        "target_folder_id": "ルール適用対象フォルダ",
        "destination_folder_id": "move or copy時の宛先フォルダ"
    }],
    // プロンプトテンプレート
    "prompt_item_requests": [{
        "id": "プロンプトテンプレートのID",
        "name": "プロンプトテンプレートの名前",
        "description": "プロンプトテンプレートの説明",
        "prompt_template": "プロンプトテンプレート",
        "prompt_template_type": "プロンプトテンプレートのタイプ",
        "extended_properties_json": "拡張プロパティ"
    }],
    // 検索リクエスト
    "search_request": {
      "description": "str",
      "content": "str",
      "tags": "str",
      "source_application_name": "str",
      "source_application_title": "str",
      "start_time_str": "str",
      "end_time_str": "str",
      "enable_start_time": "bool",
      "enable_end_time": "bool",
      "exclude_description": "bool",
      "exclude_content": "bool",
      "exclude_tags: bool",
      "exclude_source_application_name": "bool",
      "exclude_source_application_title": "bool"
    }

}
```

### response



