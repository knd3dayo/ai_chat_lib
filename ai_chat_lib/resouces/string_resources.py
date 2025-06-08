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

    prompt_item_tile_generation = "Tile Generation"

    prompt_item_tile_generation_prompt = """
    Please generate a title from the following text.
    """

    prompt_item_background_information_generation = "Background Information Generation"

    prompt_item_background_information_generation_prompt = """
    Please generate background information from the following text.
    """

    prompt_item_summary_generation = "Summary Generation"

    prompt_item_summary_generation_prompt = """
    Please generate a summary from the following text.
    - Output in bullet point format.
    - Include important information.
    """

    prompt_item_task_generation = "Task Generation"
    prompt_item_task_generation_prompt = """
    Please generate a TODO list from the following text.
    Output as a list of strings in JSON format {result:[list items]}.
    """

    prompt_item_document_relaiability_check = "Document Reliability Check"
    prompt_item_document_relaiability_check_prompt = """
        # Information Reliability Judgment
        ## Overview\r\nThe level at which information can be used as evidence for other information. 
        ## How to Judge 
        First, set the following indicators as rough guidelines. 
        ### Judgment based on the source and scope of the text 
        * If it is written by an authoritative organization, institution, or person and is generally available information, the reliability level is high (reliability: 90-100%). 
            However, further classification of sites with high reliability is required. 
        * Information from sites that require reliable information, such as Wikipedia, is of medium to high reliability (reliability: 70-90%). 
            However, further classification of sites with medium to high reliability is required. 
        * Information from sites such as StackOverflow, which may contain errors but can be checked by many people, is of low to medium reliability (reliability: 40-60%). 
        * If it is written by an organization or person within the company and the scope of disclosure is limited to the organization, the reliability level is low to high (reliability: 40-90%). 
            * Documents that are expected to be seen by many people within the organization, such as emails, Teams chats for requests or confirmations, notifications, and research presentation materials. 
            * The information may include works in progress or unreviewed information. 
        * If the assumed scope of disclosure is unknown or the text is considered to be between individuals, the reliability level is low (reliability: 10-30%). 
            * Personal ideas, memos, and texts with unclear context. 
        ### Judgment based on the content 
        * The reliability of texts at each reliability level can be influenced by their content. 
            * Information that can be determined to be correct based on existing logic, mathematical laws, or natural scientific laws should have the upper limit of reliability within the level. 
            * Information that can be determined to be somewhat correct based on general sociological laws, customs, etc. should have the middle value of reliability within the level. 
            * Information for which correctness cannot be determined and verification is required should have the lower limit of reliability within the level. 
        
        Based on the above, please determine the reliability level of the following text and output the reliability score (0-100) along with the reason for the reliability determination.;
        """
    
    # TagGeneration
    prompt_item_tag_generation = "Tag Generation"
    prompt_item_tag_generation_prompt = """
        Please generate tags that match the following text. If there are existing tags, please select them.
        - If there are no existing tags, please create new tags.
        - The output should be in JSON format as {result:['tag1', 'tag2', 'tag3']}.
    """    
    # SelectExistingTags
    prompt_item_select_existing_tags = "Select Existing Tags"
    prompt_item_select_existing_tags_prompt = """
        From the list of existing tags, please select the tags that match the following text.
        The output should be in JSON format as {result:['tag1', 'tag2', 'tag3']}.
        The list of existing tags is as follows:
        """            

    # AutoProcessItem
    auto_process_item_name_ignore = "Ignore"
    auto_process_item_description_ignore = "Ignore the item without any processing."

    auto_process_item_name_copy_to_folder = "Copy to Folder"
    auto_process_item_description_copy_to_folder = "Copy the item to the specified folder."

    auto_process_item_name_move_to_folder = "Move to Folder"
    auto_process_item_description_move_to_folder = "Move the item to the specified folder."

    auto_process_item_name_extract_text = "Extract Text"
    auto_process_item_description_extract_text = "Extract text from the item."

    auto_process_item_name_prompt_template = "Prompt Template"
    auto_process_item_description_prompt_template = "Use the prompt template to process the item."



