from typing import Any, Annotated, Union, Callable
from autogen_core.code_executor import ImportFromModule
from autogen_core.tools import FunctionTool
from autogen_agentchat.messages import BaseChatMessage
import asyncio

# execute_agent
# エージェントを実行する関数
async def execute_agent(
        agent_name: Annotated[str, "Agent name"], input_text: Annotated[str, "Input text"],
        ) -> Annotated[str, "Output text"]:
    """
    This function executes the specified agent with the input text and returns the output text.
    First argument: agent name, second argument: input text.
    - Agent name: Specify the name of the agent as the Python function name.
    - Input text: The text data to be processed by the agent.
    """
    import ai_chat_lib.log_modules.log_settings as log_settings
    logger = log_settings.getLogger(__name__)
    
    global autogen_props 
    from ai_chat_lib.db_modules import MainDB, AutogenAgent
    from ai_chat_lib.autogen_modules import AutoGenProps
    props : AutoGenProps = autogen_props # type: ignore

    agent = AutogenAgent.get_autogen_agent(agent_name)
    if agent is None:
        return "The specified agent does not exist."
    
    output_text = ""
    # run_agent関数を使用して、エージェントを実行
    import uuid
    trace_id = str(uuid.uuid4())
    async for message in props.run_agent(agent_name, input_text):
        if isinstance(message, BaseChatMessage):
            message_str = f"{message.source}(in agent selector:{trace_id}): {message.content}" # type: ignore
            logger.debug(message_str)
            output_text += message_str + "\n"   
    return output_text

# エージェント一覧を取得する関数
async def list_agents() -> Annotated[list[dict[str, str]], "List of registered agents, each containing 'name' and 'description'"]:
    """
    This function retrieves a list of registered agents from the database.
    """
    from ai_chat_lib.db_modules import AutogenAgent
    agents = await AutogenAgent.get_autogen_agent_list()
    agent_list = []
    for agent in agents:
        agent_list.append({"name": agent.name, "description": agent.description})
    return agent_list

import ast

def extract_imports(code) -> list[Union[str, ImportFromModule]]:
    """
    Pythonコードからimport文を抽出する
    引数:
    - code: Pythonコード（文字列）

    戻り値: import文のリスト
    """
    
    tree = ast.parse(code)
    imports: list[Union[str, ImportFromModule]] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module if node.module else ""
            for alias in node.names:
                imports.append(ImportFromModule(module=module, imports=[alias.name]))
    return imports


def move_imports_to_function(code, function_name):
    """
    グローバルなimport文を特定の関数内に移動する
    引数:
    - code: Pythonコード（文字列）
    - function_name: 移動先の関数名

    戻り値: 更新されたコード（文字列）
    """
    tree = ast.parse(code)

    # import文を収集
    imports = []
    body_without_imports = []

    for node in tree.body:
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            imports.append(node)
        else:
            body_without_imports.append(node)

    # 指定した関数を探す
    function_found = False
    for node in body_without_imports:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            # 関数の先頭にimport文を追加
            node.body = imports + node.body
            function_found = True

    if not function_found:
        raise ValueError(f"関数 '{function_name}' が見つかりませんでした。")

    # 残りのコード（importを削除済み）の組み直し
    tree.body = body_without_imports

    # 再構築されたコードを文字列として返す
    updated_code = ast.unparse(tree)
    return updated_code


async def list_tool_agents() -> Annotated[list[dict[str, str]], "List of registered tools, each containing 'name' and 'description'"]:
    """
    This function retrieves a list of registered tool agents.
    """
    import ai_chat_lib.log_modules.log_settings as log_settings
    logger = log_settings.getLogger(__name__)

    logger.debug('start list_tool_agents')
    global autogen_props
    from ai_chat_lib.db_modules import MainDB, AutogenTools
    tools = await AutogenTools.get_autogen_tool_list()

    tool_descption_list = []
    for agent in tools:
        tool_descption_list.append({"name": agent.name, "description": agent.description, "path": agent.path})
        logger.debug(f"tool name:{agent.name}, description:{agent.description}")

    return tool_descption_list

# FunctionToolを実行するエージェントをwork_agentsに追加
async def register_tool_agent(name: Annotated[str, "Function name"], doc: Annotated[str, "Function documentation"], 
                         code: Annotated[str, "Python Code"]) -> Annotated[str, "Message indicating that the tool agent has been registered"]:
    """
    This function creates a FunctionTool object with the specified function name, documentation, and Python code.
    引数で与えられたPythonコードからexec関数を使用して関数を作成し、FunctionToolオブジェクトを作成します。
    作成したFunctionToolを実行するためのエージェントを作成し、tool_agentsに追加します。
    """
    import ai_chat_lib.log_modules.log_settings as log_settings
    logger = log_settings.getLogger(__name__)

    global autogen_props

    import os
    from ai_chat_lib.db_modules import MainDB, AutogenTools
    from ai_chat_lib.autogen_modules import AutoGenProps
    props : AutoGenProps = autogen_props # type: ignore

    # toolsディレクトリがない場合は作成
    if not props.tool_dir_path:
        raise ValueError("tool_dir_path is not set in props.")
    python_file_path = os.path.join(props.tool_dir_path, f"{name}.py")

    # toolsディレクトリに{name}.pyとして保存
    with open(python_file_path, "w", encoding="utf-8") as f:
        f.write(code)

    await AutogenTools.update_autogen_tool(AutogenTools(name=name, description=doc, path=python_file_path))
    
    message = f"Registered tool agent: {name}"
    logger.debug(message)
    return message

# エージェントを実行する関数
async def execute_tool_agent(
        agent_name: Annotated[str, "Agent name"], initial_message: Annotated[str, "Input text"],
        ) -> Annotated[str, "Output text"]:
    """
    This function executes the specified agent with the input text and returns the output text.
    First argument: agent name, second argument: input text.
    - Agent name: Specify the name of the agent as the Python function name.
    - Input text: The text data to be processed by the agent.
    """
    import ai_chat_lib.log_modules.log_settings as log_settings
    logger = log_settings.getLogger(__name__)
    global autogen_props

    import os
    from ai_chat_lib.db_modules import MainDB, AutogenTools
    from ai_chat_lib.autogen_modules import AutoGenProps
    props : AutoGenProps = autogen_props # type: ignore

    try:
        # agent_nameに対応するエージェントを取得
        logger.debug('start execute_tool_agent')
        tool_list = [ tool for tool in await list_tool_agents() if tool["name"] == agent_name]
        tool = tool_list[0] if len(tool_list) > 0 else None

        if tool is None:
            return f"The specified agent does not exist. Agent name: {agent_name}"
        name = tool["name"]
        path = tool["path"]
        # ファイルから関数を読み込む
        func = props.load_function(path, name)
        output_text = ""
        # エージェントを作成
        agent = props.create_agent(
            name=name,
            description=f"{name}ツール実行エージェント",
            system_message=f"""
            あなたは{name}を実行するエージェントです。{name}の説明：{func.__doc__}
            """,
            tools=[
                FunctionTool(func, func.__doc__, name=name) # type: ignore
            ]
        )

        import uuid
        # 識別子を生成
        trace_id = str(uuid.uuid4())
        # run_agent関数を使用して、エージェントを実行
        async for message in agent.run_stream(task=initial_message):
            if isinstance(message, BaseChatMessage):
                message_str = f"{message.source}(in tool agent selector:{trace_id}): {message.content}" # type: ignore
                print(message_str)
                output_text += message_str + "\n"

        return output_text
    except Exception as e:
        import traceback
        logger.error(f"Error in execute_tool_agent: {e}")
        logger.error(traceback.format_exc())
        return f"Error: {e}"

    
