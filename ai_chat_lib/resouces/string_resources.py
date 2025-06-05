class StringResources:
    """
    A class to hold string resources for this library.
    """
    autogen_planner_agent_description = """
    Think of a plan to achieve the user's request and cooperate with each agent to accomplish the request.
    """

    autogen_planner_agent_system_message = """
    Think of a plan to achieve the user's request and cooperate with each agent to accomplish the request.
    - Create a plan and a list of tasks to achieve the user's request.
    - If there are any issues with task assignments or if there is a more efficient plan or task assignment, confirm with the relevant agent.
    - Assign tasks to the relevant agents based on the plan.
    - When the plan is complete, reply with [Plan Completed].
    After that, execute the tasks according to the plan. When all tasks are complete, reply with [TERMINATE].
    """

    autogen_default_group_chat_description = """
    Think of a plan to achieve the user's request and cooperate with each agent to accomplish the request.
    """
