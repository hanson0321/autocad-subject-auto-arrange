import matplotlib.pyplot as plt
def flatten_list(original_list):
    # Initialize a new list to hold the flattened list of lists
    flattened_list = []

    # Loop through each tuple in the original list
    for tuple_pair in original_list:
        # Extend the new list with each list in the tuple
        flattened_list.extend(tuple_pair)

    # Print the new flattened list
    return flattened_list

def plot(list):
    print("Plotting")
    fig, ax = plt.subplots()
    for i in flatten_list(list):
        x, y = zip(*i)
        ax.plot(x,y, 'r-', linewidth =0.5)

    ax.set_aspect('equal', adjustable = 'box')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('DXF Display')
    plt.grid(True)
    plt.show()

def plot_flattened(list):
    print("Plotting")
    fig, ax = plt.subplots()
    for i in list:
        x, y = zip(*i)
        ax.plot(x,y, 'r-', linewidth =0.5)

    ax.set_aspect('equal', adjustable = 'box')
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.title('DXF Display')
    plt.grid(True)
    plt.show()