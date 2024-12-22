import operator
import sqlite3
import pandas as pd
from subprocess import call
from typing import TypedDict, Annotated, List, Callable
from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver
from recorder import AudioRecorder
import os

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

class SmartAssistant:
    def __init__(
        self,
        model: ChatOpenAI,
        tools: List[Callable],
        db_uri: str
    ):
        self.model = model
        self.tools = tools
        self.system_prompt = self.load_system_prompt("configs/system_prompt.txt")
        self.recorder = AudioRecorder()
        self.db_uri = db_uri
        self.checkpointer = None
        self.load_checkpointer()
        self.agent = self.create_agent()
    
    def load_checkpointer(self):
        conn = sqlite3.connect(self.db_uri, check_same_thread=False)
        self.checkpointer = SqliteSaver(conn)
    
    def load_system_prompt(self, soul_file_path):
        with open(soul_file_path, "r") as file:
            soul = file.read()
        return soul
    
    def talk(self, text):
        call(["python", "src/speak.py", text])

    def llm_node(
        self,
        state: AgentState
    ):
        model_with_tools = self.model.bind_tools(self.tools)
        messages = state['messages']
        messages = [SystemMessage(content=self.system_prompt)] + messages
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
        conn = sqlite3.connect(self.db_uri, check_same_thread=False)
        try:
            df = pd.read_sql_query("SELECT thread_id FROM checkpoints", conn)
            last_id = df['thread_id'].astype(int).max()
        except:
            last_id = 0
        new_id = f"{last_id+1:05}"
        config = {"configurable": {"thread_id": new_id}}
        self.agent.invoke({'messages': []}, config=config)
