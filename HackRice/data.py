import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
import openai

openai.api_key_path='api_key.txt'
def generate_text(prompt, max_tokens=70):
    print(prompt)
    prompt="Please analyse this csv about my transportation habits.\n"+prompt+"\n Concisely provide me any actionable recommendations?"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a data analyst assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=max_tokens
    )
    generated_text = response.choices[0].message["content"]

    return generated_text

# Creates a line graph to show transportation habits over time.
def query_user_stats(user_name, csv_data):

    # Looks for the specific user in a specific data table using the parameters above.
    user_data = csv_data[csv_data.user == user_name]
    user_data.set_index('date', inplace=True)

    # Creates a date range for the times transportation metrics were tracked.
    user_walk = user_data.miles_walked
    user_walk.index = pd.DatetimeIndex(user_walk.index)

    user_pool = user_data.miles_on_publict
    user_pool.index = pd.DatetimeIndex(user_pool.index)

    user_car = user_data.miles_on_car
    user_car.index = pd.DatetimeIndex(user_car.index)

    user_walk = user_walk.reindex(pd.date_range(user_walk.index[0], user_walk.index[-1]))
    user_pool = user_pool.reindex(pd.date_range(user_pool.index[0], user_pool.index[-1]))
    user_car = user_car.reindex(pd.date_range(user_car.index[0], user_car.index[-1]))

    # Plots the graph, as well as creates other graph features.
    plt.figure(figsize = (9,5))
    plt.title('Types of Transportation', size=15,weight='bold',y=1.03)
    plt.xticks(rotation=30)
    plt.ylabel('Miles', size=10, weight='bold', labelpad=20)
    ax = plt.subplot()
    ax.set_axisbelow(True)
    ax.xaxis.grid(color='gray', linestyle='dashed')
    ax.yaxis.grid(color='gray', linestyle='dashed')
    plt.plot(user_walk.index, user_walk, marker='o', c='lime')
    plt.plot(user_pool.index, user_pool, marker='o', c='c')
    plt.plot(user_car.index, user_car, marker='o', c='r')
    plt.legend(labels=['Walked', 'Public Transport', 'Private Transport'])

    # Formats the datetime format into legible strings, then labels that as the x-axis label
    # Also formats the dates to allocate for dates where data was not entered.
    date_format = []
    for item in user_walk.index:
        date_format.append(item.strftime("%m/%d/%Y"))
    plt.xticks(ticks=user_walk.index, labels=date_format)

    # Displays the chart.
    plt.show()
    # plt.savefig('images/user_trend.png')
    return 'images/user_trend.png'

# Creates a pie-chart graphic showing the total amount travelled by various transportation modes.
def query_user_pie(user_name, csv_data):

    # Finds the specific user, and then creates a cumulative sum of the various types of transport.
    user_data = csv_data[csv_data.user == user_name]
    user_walk = user_data.miles_walked.cumsum().tail(1).reset_index(drop=True)[0]
    user_pool = user_data.miles_on_publict.cumsum().tail(1).reset_index(drop=True)[0]
    user_car = user_data.miles_on_car.cumsum().tail(1).reset_index(drop=True)[0]

    user_values=[user_walk, user_pool, user_car]
    user_labels=['Walked', 'Public Transport', 'Private Transport']

    # Function to format the pie chart to show percentage and frequency values.
    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct*total/100.0))
            return '{p:.2f}%  ({v:d})'.format(p=pct,v=val)
        return my_autopct

    # Plots the pie chart.
    plt.pie(user_values, colors=['lime','c','r'], labels=user_labels, autopct=make_autopct(user_values),
            wedgeprops = {"edgecolor" : "black",'linewidth': 1.3})
    plt.title('Cumulative Transportation Total', fontweight='bold')
    # plt.savefig('images/user_pie.png')
    plt.show()
    return 'images/user_pie.png'

def render_graphs(df, username):
    return [query_user_pie(username,df),query_user_stats(username,df)]