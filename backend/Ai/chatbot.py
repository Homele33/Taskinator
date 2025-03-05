




# from ollama import chat, ChatResponse, Client


# client = Client()

# res = client.create(
#     model="my-task-assistant",
#     from_="llama3.2",
#     system="you help break down tasks to subtasks.",
#     stream=False,
# )

# print(res.status)

# response = client.chat(model="my-task-assistant", messages=[
#     {
#         "role": "user",
#         "content": "implement python backend with LLM using ollama"
#     }
# ])

# print(response.message.content)
# # response: ChatResponse = chat(model="llama3.2",messages=[
# #     {
# #         "role": "user",
# #         "content": "implement python backend for the LLM",
# #     },
# # ])
# # print(response["message"]['content'])