
from owlready2 import *
import logging
import signal, sys, os
from threading import Lock
from datetime import datetime
from ament_index_python.packages import get_package_share_directory

class SysSelf:

    def __init__(self, owl_path, owl_names):
        self.onto = None     # owl model
        self.owl_path = owl_path
        self.owl_names = owl_names
        
        signal.signal(signal.SIGINT, self.save_ontology_exit)
        self.ontology_lock = Lock() 

    def perform_reasoning(self):
        return_value = False
        with self.ontology_lock:
            with self.onto:
                try:
                    sync_reasoner_pellet(infer_property_values = True, infer_data_property_values = True, debug = 0)
                    print("----------Reasoner executed------------")
                    return_value = True
                except Exception as err:
                    logging.exception("{0}".format(err))
                    return False
                    # raise err

        return return_value

    # For debugging purposes: saves the runtime ontology in file
    def save_ontology_exit(self, signal, frame):
        # self.get_logger().info("----------Saving current ontology log------------")
        now = datetime.now()
        formatted_date = now.strftime("%Y-%m-%d_%H-%M-%S")
        file_str = "log_owl_" + formatted_date + ".owl"
        self.onto.save(file=file_str, format="rdfxml")
        sys.exit(0)


    def load_OWL_file(self):
        try:
            onto_partial = []
            for file in (self.owl_names):
            # if this raise errors, check owl:imports in owl_file, it should be the URI ending in /
                path_new = self.owl_path + "/" + file
                onto_path.append(self.owl_path) # add ontology dependencies
                onto_partial.append(get_ontology(path_new).load())

            self.onto = onto_partial[0] # the first ontology loaded must be sysSelf
            # load also domain and systems ontology
            self.onto.imported_ontologies.append(onto_partial[1])
            self.onto.imported_ontologies.append(onto_partial[2])
            
        except Exception as e:
            logging.exception("{0}".format(e))
            return None
        
    def get_relations(self):
        # self.perform_reasoning()
        print((self.onto.Component.instances()))

    # def yoneda_lemma(self):
    #     # get all relationships on the capability / component / goal we are going to substitute
    #     # decide the reconfig

    # def push_out(self):
        # detect the entities affected by a contingency AND the entities affected by a change
    
    # def change_status(self, individual, value):
    #     #TODO


path = os.path.join(get_package_share_directory('sys_self_mc'), 'ontologies')
names = ["sys_self.owl","rm_domain.owl", "app_loc.owl"]
clase = SysSelf(path, names)
clase.load_OWL_file()
clase.get_relations()