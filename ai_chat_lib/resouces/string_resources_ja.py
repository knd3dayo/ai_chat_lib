from .string_resources import StringResources

class StringResourcesJa(StringResources):
    """
    A class to hold string resources for this library.
    """
    autogen_planner_agent_description = """
    ユーザーの要求を達成するための計画を考えて、各エージェントと協力して要求を達成します
    """

    autogen_planner_agent_system_message = """
    ユーザーの要求を達成するための計画を考えて、各エージェントと協力して要求を達成します
    - ユーザーの要求を達成するための計画を作成してタスク一覧を作成します。
    - タスクの割り当てに問題ないか？もっと効率的な計画およびタスク割り当てがないか？については対象エージェントに確認します。
    - 計画に基づき、対象のエージェントにタスクを割り当てます。
    - 計画作成が完了したら[計画作成完了]と返信してください
    その後、計画に基づきタスクを実行します。全てのタスクが完了したら、[TERMINATE]と返信してください。
    """

    autogen_default_group_chat_description = """
    ユーザーの要求を達成するための計画を考えて、各エージェントと協力して要求を達成します
    """

    prompt_item_tile_generation = "タイトル生成"

    prompt_item_tile_generation_prompt = """
    以下のテキストからタイトルを生成してください。
    """

    prompt_item_background_information_generation = "背景情報生成"

    prompt_item_background_information_generation_prompt = """
    以下のテキストから背景情報を生成してください。
    """

    prompt_item_summary_generation = "要約生成"

    prompt_item_summary_generation_prompt = """
    以下のテキストから要約を生成してください。
    - 箇条書き形式で出力してください。
    - 重要な情報を含めてください。
    """

    prompt_item_task_generation = "タスク生成"
    prompt_item_task_generation_prompt = """
    以下のテキストからTODOリストを生成してください。
    出力はJSON形式で{result:[リスト項目]}としてください。
    """

    prompt_item_document_relaiability_check = "ドキュメント信頼性チェック"
    prompt_item_document_relaiability_check_prompt = """
        # 情報の信頼性判断
        ## 概要
        他の情報の根拠として利用できるレベル。
        ## 判断方法
        まず、以下の指標を大まかな目安としてください。
        ### テキストの出所や公開範囲による判断
        * 権威ある組織・機関・人物が執筆し、一般に公開されている情報は信頼性が高い（信頼性：90-100%）。
            ただし、信頼性の高いサイト内でも更なる分類が必要です。
        * Wikipediaなど信頼性が求められるサイトの情報は中〜高程度の信頼性（信頼性：70-90%）。
            ただし、中〜高程度のサイト内でも更なる分類が必要です。
        * StackOverflowなど誤りが含まれる可能性があるが多くの人が確認できるサイトの情報は低〜中程度の信頼性（信頼性：40-60%）。
        * 社内の組織や人物が執筆し、公開範囲が組織内に限定されている場合は低〜高程度の信頼性（信頼性：40-90%）。
            * 社内で多くの人が目にすることが想定されるメール、Teamsチャットでの依頼・確認、通知、研究発表資料など。
            * 作業途中や未確認の情報が含まれる場合があります。
        * 公開範囲が不明、または個人間のやりとりと考えられるテキストは信頼性が低い（信頼性：10-30%）。
            * 個人的な考えやメモ、文脈が不明瞭なテキストなど。
        ### 内容による判断
        * 各信頼性レベルのテキストでも内容によって信頼性が上下します。
            * 既存の論理や数学的法則、自然科学的法則から正しいと判断できる情報は、そのレベルの上限値としてください。
            * 一般的な社会的法則や慣習などからある程度正しいと判断できる情報は、そのレベルの中央値としてください。
            * 正しさが判断できず検証が必要な情報は、そのレベルの下限値としてください。

        上記を踏まえ、以下のテキストの信頼性レベルを判断し、信頼性スコア（0-100）とその理由を出力してください。
        """
    
    # TagGeneration
    prompt_item_tag_generation = "タグ生成"
    prompt_item_tag_generation_prompt = """
        以下のテキストに合うタグを生成してください。既存のタグがあれば選択してください。
        - 既存のタグがなければ新しいタグを作成してください。
        - 出力はJSON形式で{result:['tag1', 'tag2', 'tag3']}としてください。
    """    
    # SelectExistingTags
    prompt_item_select_existing_tags = "既存タグ選択"
    prompt_item_select_existing_tags_prompt = """
        既存のタグ一覧から、以下のテキストに合うタグを選択してください。
        出力はJSON形式で{result:['tag1', 'tag2', 'tag3']}としてください。
        既存のタグ一覧は以下の通りです：
        """            

    # AutoProcessItem
    auto_process_item_name_ignore = "無視"
    auto_process_item_description_ignore = "このアイテムを処理せずに無視します。"

    auto_process_item_name_copy_to_folder = "フォルダーにコピー"
    auto_process_item_description_copy_to_folder = "アイテムを指定したフォルダーにコピーします。"

    auto_process_item_name_move_to_folder = "フォルダーに移動"
    auto_process_item_description_move_to_folder = "アイテムを指定したフォルダーに移動します。"

    auto_process_item_name_extract_text = "テキスト抽出"
    auto_process_item_description_extract_text = "アイテムからテキストを抽出します。"

    auto_process_item_name_prompt_template = "プロンプトテンプレート"
    auto_process_item_description_prompt_template = "プロンプトテンプレートを使ってアイテムを処理します。"
