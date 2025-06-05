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
