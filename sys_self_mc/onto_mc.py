
from owlready2 import get_ontology, destroy_entity, sync_reasoner_pellet, onto_path
import logging
import signal, sys
from threading import Lock
from datetime import datetime

class SysSelf:

    def __init__(self, app_file):
        self.onto = None       # owl model
        self.owl_file = app_file
        signal.signal(signal.SIGINT, self.save_ontology_exit)
        self.ontology_lock = Lock()
        self.isInitialized = True

    def perform_reasoning(self):
        return_value = False
        with self.ontology_lock:
            with self.onto:
                try:
                    sync_reasoner_pellet(infer_property_values = True, infer_data_property_values = True)
                    return_value = True
                except Exception as err:
                    logging.exception("{0}".format(err))
                    return False
                    # raise err

        return return_value

    # For debugging purposes: saves the runtime ontology in file
    def save_ontology_exit(self):
        now = datetime.now()
        formatted_date = now.strftime("%Y-%m-%d_%H-%M-%S")
        file_str = "rt_owl_" + formatted_date + ".owl"
        self.onto.save(file=file_str, format="rdfxml")
        sys.exit(0)


    def load_OWL_file(self):
        try:
            # if this raise errors, check owl:imports in owl_file, it should be the URI ending in /
            onto_path.append("/home/esther/robominers_ws/src/sysself/ontologies/") # add ontology dependencies
            print(self.owl_file)
            self.onto = get_ontology(self.owl_file).load()
            print("LOADED")
        except Exception as e:
            logging.exception("{0}".format(e))
            return None
        


### main
ss = SysSelf("/home/esther/robominers_ws/src/sysself/ontologies/rm_domain.owl")
ss.load_OWL_file()
a = ss.onto.search(iri = "*Nav*")
print(list(a))


# TODO fix ontology paths

