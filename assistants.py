import operator
import yaml
import sqlite3
import pandas as pd
from subprocess import call
from dotenv import load_dotenv
from typing import TypedDict, Annotated, List, Callable
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver
from recorders import AudioRecorder
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

class SmartAssistant:
    def __init__(
        self,
        config_path: str,
        model: ChatOpenAI,
        tools: List[Callable],
        db_uri: str
    ):
        config = self.load_config(config_path)
        self.model = model
        self.tools = tools
        self.soul = self.load_soul(config['soul_file_path'])
        self.recorder = AudioRecorder()
        self.db_uri = db_uri
        self.checkpointer = None
        self.load_checkpointer()
        self.agent = self.create_agent()

    def load_config(self, config_path):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    
    def load_checkpointer(self):
        with SqliteSaver.from_conn_string(self.db_uri) as sqlite_checkpointer:
            self.checkpointer = sqlite_checkpointer
    
    def load_soul(self, soul_file_path):
        with open(soul_file_path, "r") as file:
            soul = file.read()
        return soul
    
    def talk(self, text):
        call(["python", "speak.py", text])

    def llm_node(
        self,
        state: AgentState
    ):
        model_with_tools = self.model.bind_tools(self.tools)
        messages = state['messages']
        messages = [SystemMessage(content=self.soul)] + messages
        message = model_with_tools.invoke(messages)
        talk_message = message.copy()
        talk_message.content = message.content if not message.content.endswith('FINE') else message.content[:-4]
        talk_message.pretty_print()
        self.talk(talk_message.content)
        return {'messages': [message]}

    def router(self, state: AgentState):
        result = state['messages'][-1]
        if len(result.tool_calls) > 0:
            return "tool"
        elif result.content.endswith("FINE"):
            return "end"
        else:
            return "human"

    def human_node(self, state: AgentState):
        request = self.recorder.listen()
        # request = input('listening: ')
        message = HumanMessage(content=request)
        message.pretty_print()
        return {'messages': [message]}
    
    def create_agent(self):

        graph = StateGraph(AgentState)
        graph.add_node("llm", self.llm_node)
        graph.add_node("tool", ToolNode(self.tools))
        graph.add_node("human", self.human_node)
        graph.add_conditional_edges(
            "llm",
            self.router,
            {
                "tool": "tool", 
                "end": END,
                "human": "human"
            }
        )
        graph.add_edge("tool", "llm")
        graph.add_edge("human", "llm")
        graph.set_entry_point("human")
        if self.checkpointer is not None:
            agent = graph.compile(checkpointer=self.checkpointer)
        else:
            agent = graph.compile()
        return agent
    
    def run(self):
        conn = sqlite3.connect(self.db_uri)
        df = pd.read_sql_query("SELECT thread_id FROM checkpoints", conn)
        last_id = df['thread_id'].astype(int).max()
        new_id = f"{last_id+1:05}"
        config = {"configurable": {"thread_id": new_id}}
        self.agent.invoke({'messages': []}, config=config)

if __name__ == "__main__":
    from tools import (
        add_shopping_list,
        leggi_oroscopo,
        invia_messaggio,
        read_shopping_list
    )
    model = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4"
    )
    agent = SmartAssistant(
        config_path='configs/config.yaml',
        model=model,
        tools=[add_shopping_list, leggi_oroscopo, invia_messaggio, read_shopping_list],
        db_uri='checkpoint.db'
    )
    agent.run()