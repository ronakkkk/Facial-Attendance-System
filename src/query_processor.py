from .dbutils import create_connection, run_query_noreturn
from .queries import check_faces

class QueryProcessor:

    def __init__(self, databases):
        self.connection_container = {_id:create_connection(path) for _id, path in databases}

    def _process_query(self, query_details):

        command, db_id, query_type, query, value = query_details
        
        ret_val = None
        if command is None:
            if query_type == 'fetch':
                pass
            else:
                run_query_noreturn(self.connection_container[db_id], query, value)

        else:
            ret_val = eval(command)(self.connection_container[db_id], *value)
            
        return command,ret_val


    def process_queries(self, control_panel, db_memory):
        
        while (not control_panel.should_stop()) and (not control_panel.is_close_all()):
            
            query_details = db_memory.get_query()

            if query_details:
                command, val = self._process_query(query_details)
                if command == 'check_faces' and val is not None:
                    if val == 'welcome':
                        control_panel.set_welcome_announcement()
                    if val == 'guard':
                        control_panel.set_guard_announcement()
        
        print('Running cleanup query')
        
        #Clean up code
        while 1:
            query_details = db_memory.get_query()
            if query_details:
                self._process_query(query_details)
            else:
                break

        for key in self.connection_container:
            self.connection_container[key].close()
    
    def process_offline_queries(self, db_memory):
        
        while 1:

            query_details = db_memory.get_query()

            if query_details:            
                command = query_details[0]
                if command == 'terminate':
                    break
                #Uncomment to process queries like check_faces    
                # self._process_query(query_details)
        
        for key in self.connection_container:
            self.connection_container[key].close()
