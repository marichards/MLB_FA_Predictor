def ModelIt(fromUser = 'Default', free_agents = []):
    in_month = len(free_agents)
    print("The number born is %i" % in_month)
    result = in_month
    if fromUser != 'Default':
        return result
    else:
        return 'check your input'
