from ball23 import TippeData
import matplotlib.pyplot as plt

if __name__ == "__main__":
    ball = TippeData()
    ball.update()
    data = ball.get_sorted_dict()

    for name in data.keys():
        print(f"{name}: {data[name]['points_history']}")
        plt.plot(data[name]['points_history'],label=name)

    plt.title("history")
    plt.grid()
    plt.legend()
    plt.show()
