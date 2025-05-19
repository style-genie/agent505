import logging
logger = logging.getLogger(__name__)
import litellm
import json
import subprocess
import time
import os
import sys
from pathlib import Path
from dotenv import dotenv_values
import asyncio
from litellm import completion 
from pydantic import BaseModel, create_model
from uuid import uuid4
uuid_4config = dotenv_values(Path(__file__).parent.parent.parent / ".env")
# todo
# for key, value in config.items():
#     os.environ[key] = value
# the reason i have this function here is that mcp functions can call this too


class ModelUtils:
    """
    ModelContextProtocol:
        The ModelContextProtocol class provides a protocol for interacting with models in a session.
        It manages the registration of models, providers, and hosts, and provides methods for sending messages to models and handling errors.
    
        Attributes:
            manager: The manager object that manages the session.
            session_id_: A unique identifier for the session.
            models: A dictionary of models available for use in the session.
            POSTGRES_USER: The PostgreSQL user for the session.
            POSTGRES_PASSWORD: The PostgreSQL password for the session.
            POSTGRES_DB: The PostgreSQL database for the session.
            PINECONE_API_KEY: The Pinecone API key for the session.
            INDEX_HOST: The index host for the session.
            NAMESPACE: The namespace for the session.
    
        Methods:
            __init__: Initializes the model context protocol with a manager and session ID.
            error: Handles errors by sending an error message to the client and printing the error.
            register_provider: Registers a provider with the model context protocol.
    """
    def error(self,error):
        if(self.manager):
            self.manager.send_personal_message(self.session_id_, {"message": f"Error received: {error}"})
            print(f"Error received: {error}")
        #raise ValueError(error)
    def __init__(self,manager,session_id_):
        self.models = {}
        self.session_id_ = session_id_
        self.manager = manager
   
    def compl(self, messages, agent, args_override={}, allow_tools=True):
        """Tests parallel function calling."""
        print("-----------------> Completion <----------------------")
        
        args=agent.args
        args["messages"] = messages
        for arg in args_override:
            args[arg] = args_override[arg]

        response = litellm.completion(**args)
        response = dict(response)
        
        allow_tools=allow_tools and len(agent.schemas)>0
        
        try:
            response_message = response["choices"][0].message.content
            #json_response = json.loads(response_message)    
            print("------------------R-----------------------")
            print("\nLLM Response:\n")
            print(response_message)
            print("------------------R----------------------")
            messages.append(response_message)  # extend conversation with assistant's reply
        except Exception as e:
            print("------------------E-----------------------")
            print(e)
            print("------------------E-----------------------")
            return {"error": "Unexpected response format from the model."}
        
        if allow_tools:
            tool_calls =  response_message.tool_calls
            print("\nLength of tool calls", (tool_calls)) 

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = agent.functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "get_json_element_by_id_":
                    function_response = function_to_call(id_=function_args.get("id_"))
                else:
                    function_response = function_to_call(query=function_args.get("query"))
                    
                messages.append(
                    {
                        "tool_call_id_": tool_call.id_,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    }
                )  # extend conversation with function response
                
        return {"response":response_message,"messages":messages}

class BaseAgentModel(BaseModel):
    requiresUserResponse: int
    requiresToolResponse: int
    # hier weitere felder

class Agent():
    """
    Agent:
        The Agent class represents an autonomous entity that interacts with a session and a model to process messages and provide responses.
        It manages its own state and uses the model to generate responses to input messages.
        The agent can be configured to wait for specific responses from users or tools before taking action.
    
        Attributes:
            session: The session object that the agent is associated with.
            id_: A unique identifier for the agent.
            modelid_: The ID of the model used by the agent.
            working: A flag indicating whether the agent is currently working.
            waiting: A flag indicating whether the agent is waiting for a response.
    
        Methods:
            __init__: Initializes the agent with a session, name, model ID, and other parameters.
            waitTillReady: Waits until the agent is ready to process messages.
            checkIfready: Checks if the agent is ready to process messages.
            update: Updates the agent's state based on a received message.
            get_messages: Returns the agent's messages from the session's context registry.
            clear_messages: Clears the agent's messages from the session's context registry.
            checkCompletionStatus: Checks the completion status of a message and updates the agent's state if necessary.
            send: Sends a message to the session manager.
            compl_send: Sends a message to the model and updates the agent's state with the response.
            run: Runs the feedback loop by sending a message to the model with the agent's current state and receiving a response.
    """

    def  __init__(self, session,name,provider="openrouter",tools={},default_model="openrouter/meta-llama/llama-4-scout" ,api_key=None,host_url="https://api.openrouter.ai",args={}, pydantic_response=False, loop=False,system_isntructions=["you are a helpful assistant"]):
        self.session=session
        self.id_=(f"{name}_{str(uuid4())}")
        self.working=True
        self.waiting=False
        self.system_isntructions=system_isntructions
        self.args=args
        self.loop=loop
        self.functions={}
        self.schemas=[]
        self.provider=provider
        self.default_model=default_model
        self.api_key=api_key
        self.host_url=host_url
        self.advisor_instruction="advisor is currently happy with your work! keep on!"
        try:
            new_host={f"{id}":{
                        "litellm_provider": provider,
                        "max_tokens": 8192,
                        "api_key": api_key,
                    }}
            print(new_host)
            # we use base_url since api_base seems to be a deprecated argument
            litellm.register_model(new_host)
            print(f"Registered model: {id}")
        except Exception as e:
            print(f"Failed to register host {provider}: {e}")
            sys.exit(1)
            
        for tool in tools:
            self.functions[tool["name"]]=tool["function"]
            self.schemas.append(tool["schema"])
        args={
            "model":default_model,
            "api_key":api_key,
            **args
        }
        allow_tools=len(self.schemas)>0
        if host_url:
            print(f"baseurl: {host_url}")
            args["base_url"]=host_url
        if(allow_tools):
            args["tools"] = tools
            args["tool_choice"] = "auto"
            print(tools.keys())

        if(pydantic_response):
            self.pydantic_response=pydantic_response
            self.recent_tool_response=False # we let the agent know that it has received a tool response
            self.recent_user_response=False # same goes for user response
            self.requiresUserResponse=False # also needs a response field in the pydantic response body
            self.requiesToolResponse=False  # same goes here
            AgentModel = create_model('AgentModel', foo=str, bar=(int, 123))
        
        session.contextRegistry.register_recipient("agent",self.id_)

    
    async def waitTillReady(self):
        while(self.checkIfready() == False):
            await asyncio.sleep(1)
            print(f"agent {self.id_} is not ready yet, sleeping")
        print(f"agent {self.id_} is ready")

        self.waiting=False
        self.run()

    def checkIfready(self):
        user=False
        tool=False
        working=self.working==False
        if(self.requiresUserResponse and self.recent_user_response):
            user=True
            self.requiresUserResponse=False
            self.recent_user_response=False
        if(self.requiesToolResponse and self.recent_tool_response):
            self.requiesToolResponse=False
            self.recent_tool_response=False
            tool=True
        if(user and tool and working):
            return True
        else:
            return False
        
    def update(self,msg):
        self.session.contextRegistry.update_agent(self.id_,msg)
        #   ----> check if need to wait for tool/user <----
        if(self.pydantic_response):
            self.checkCompletionStatus(msg)
            if(self.requiresUserResponse==True):
                if(msg.role=="user"):
                    self.recent_user_response=True
                else:
                    print("agent still waiting for user response")
                    self.working =False
            
            if(self.requiesToolResponse==True):
                if(msg.role=="tool"):
                    self.recent_tool_response=True
                else:
                    print("agent still waiting for tool response")
                    self.working =False
        #     ----> create sleeping task if needed <----
        if(self.checkIfready() == False):
            if(self.waiting == True):
                print("agent already busy")
                return
            else:
                self.waiting=True
                self.working=False
                asyncio.create_task(self.waitTillReady())
        elif(self.loop):
        #       ----> run feedback loop if ready <----
            self.run()
            
    def get_messages(self):
        return self.session.contextRegistry.agentMessages[self.id_]
    
    def clear_messages(self):
        self.session.contextRegistry.agentMessages[self.id_]=[]
        
    def checkCompletionStatus(self,msg):
        if(self.pydantic_response):
            if(msg.requiresUserResponse>0.5):
                self.requiresUserResponse=True
            if(msg.requiresToolResponse>0.5):
                self.requiesToolResponse=True
                
    def send(self,msg,method="response"):
        self.session.send(self.session.manager,self.session.session_id_,msg,self.id_,method_response=method)
  
    def compl(self,msg,args_overwrite={}):
        resp= self.session.manager.ModelUtils.compl(msg,self,args_overwrite)
        self.session.contextRegistry.agentMessages[self.id_].append(resp)
        self.update(resp)
        return resp
    
    #       ----> run the feedback loop <----
    def run(self):
        """
        run:
            Runs the feedback loop by sending a message to the model with the agent's current state and receiving a response.
            The message includes the agent's last 8 messages, the current plan, user data, important notes, and any advisor instructions.
            The response is then processed and used to update the agent's state.
        """
        messages=[]
        last8= self.session.contextRegistry.agentMessages[self.id_][-8:]
        plan={"role":"plan","content": self.session.contextRegistry.plan}
        data={"role":"user_data","content": self.session.contextRegistry.data}
        important_notes={"role":"important_notes","content": self.session.contextRegistry.important_notes}
        advisor_instruction={"role":"advisor_instruction","content": self.session.advisor_instruction}
        messages.extend([plan,data,important_notes,advisor_instruction]) #history
        messages.extend(last8)
        resp=self.compl(messages)
        self.send(resp,"response")

class ContextRegistry():
    """
    ContextRegistry:
        The ContextRegistry class manages the context and state of a session, including messages, plans, user data, and other relevant information.
        It provides methods for updating and retrieving context information, as well as registering recipients (e.g. agents, crews) to receive messages.
    
        Attributes:
            session: The session object that the context registry is associated with.
            agentMessages: A dictionary of messages for each agent, keyed by agent ID.
            toolCalls: A list of tool calls.
            userMessages: A list of user messages.
            crewMessages: A dictionary of messages for each crew, keyed by crew ID.
            plan: The current plan.
            important_notes: Important notes.
            history: The session history.
            data: User data.
    
        Methods:
            __init__: Initializes the context registry with a session.
            register_recipient: Registers a recipient (e.g. agent, crew) to receive messages.
            update_agent: Updates the messages for a specific agent.
            update_crew: Updates the messages for a specific crew.
            update_tool: Updates the tool calls.
            update_user: Updates the user messages.
            get_crew: Returns the messages for a specific crew.
            get_user: Returns the user messages.
            get_tool: Returns the tool calls.
            get_agent: Returns the messages for a specific agent.
            update: Updates the context registry with new information.
    """
    def __init__(self,session):
        self.session=session
        self.agentMessages={}
        self.toolCalls=[]
        self.userMessages=[]
        self.crewMessages={}
        self.plan=""
        self.important_notes=""
        self.history=""
        self.data={}
    #    ----> register_recipient <----
    def register_recipient(self,_type,id_):
        if(_type=="agent"):
            self.agentMessages[id_]=[]
        elif(_type=="crew"):
            self.crewMessages[id_]=[]
        else:
            print("unknown recipient type")
    #       ----> setters <----
    def update_agent(self,id_,msg):
        self.agentMessages[id_].append(msg)
        self.session.agents[id_].update(msg)
    def update_crew(self,id_,msg):
        self.session.crews[id_].update(msg)
        self.crewMessages[id_].append(msg)
    def update_tool(self,id_,msg):
        self.toolCalls[id_].append(msg)
    def update_user(self,id_,msg):
        self.userMessages[id_].append(msg)
    #       ----> getters <----
    def get_crew(self,id_):
        return self.crewMessages[id_]
    def get_user(self,id_):
        return self.userMessages[id_]
    def get_tool(self,id_):
        return self.toolCalls[id_]
    def get_agent(self,id_):
        return self.agentMessages[id_]
    
    # ----> main update function <----
    def update(self,msg):
        method=msg.method
        role=msg.role
        content=msg.content
        if(method=="response"):
            # Agent or Crew is receiving a Message
            receipient=msg.receipient
            if(role=="user"):
                self.update_user(receipient,msg)
            elif(role=="tool"):
                self.update_tool(receipient,msg)
            if(receipient.split("_")[0]=="agent"):
                self.update_agent(receipient,msg)
            elif(receipient.split("_")[0]=="crew"):
                self.update_crew(receipient,msg)
            else:
                print("unknown receipient")
        # User is updating stuff, or something else happens that is not directly agent related                            
        elif(method=="updateUserSettings"):
            self.session.contextRegistry.user_data=msg
            
class MessageManager():
    """
    MessageManager:
        The MessageManager class manages the receipt and processing of messages in a session.
        It provides methods for listening for incoming messages and updating the session's context registry.
    
        Attributes:
            session: The session object that the message manager is associated with.
            task: The task object that runs the listener loop.
    
        Methods:
            __init__: Initializes the message manager with a session.
            listener: Listens for incoming messages and updates the session's context registry.
            init: Initializes the message manager and starts the listener loop.
            stop: Stops the listener loop and cancels the task.
    """
    async def listener(self):
        try:
            while True:
                    msg= await self.session.websocket.receive_text()
                    print(msg)
                    msg=json.loads(msg)
                    msg=msg.msg
                    self.session.contextRegistry.update(msg)
                    asyncio.sleep(10)
        except Exception as e:
            print(e)
            asyncio.sleep(1)
    def init(self,session):
        self.session=session
        self.task=None
        self.task=asyncio.create_task(self.listener())
        
    def stop(self):
        self.task.cancel()
        self.task=None
        print("listener stopped")
        
    

class Session():
    """
    Session:
        The Session class represents a session, which is a container for a conversation or interaction between a user and a model.
        It manages the context and state of the conversation, including agents, crews, models, and messages.
    
        Attributes:
            manager: The manager object that manages the session.
            websocket: The websocket object that handles communication with the client.
            session_id_: A unique identifier for the session.
            models: A dictionary of models available for use in the session.
            max_recursion_depth: The maximum recursion depth for the session.
            agents: A dictionary of agents in the session, keyed by agent ID.
            crews: A dictionary of crews in the session, keyed by crew ID.
            contextRegistry: The context registry for the session.
            messageManager: The message manager for the session.
    
        Methods:
            __init__: Initializes the session with a manager, websocket, and session ID.
    """
    def __init__(self, manager,websocket,session_id_):
        """
        Initializes the session with a manager, websocket, and session ID.

        Parameters
        ----------
        manager : Manager
            The manager object that manages the session.
        websocket : WebSocket
            The websocket object that handles communication with the client.
        session_id_ : str
            The session identifier for the current interaction.
        """
        self.manager = manager
        self.websocket = websocket
        self.session_id_ = session_id_
        self.agents={}
        self.crews={}
        self.modelUtils = ModelUtils(self.manager,self.session_id_)
        self.contextRegistry=ContextRegistry(session=self)
        self.messageManager=MessageManager(self)        















# database_manager:
#   role: >
#     {topic} Senior Data Researcher
#   goal: >
#     Find the most relevant items using intelligent vector semantic search
#   backstory: >
#     You're a trained data analyst who accesses the vector database and finds the most relevant {topic} items.
#     You want to help the user finding suiting items and therefore you know how to find the right keywords. 
#     Known for your ability to find the most relevant
#     information and present it in a clear and concise manner.