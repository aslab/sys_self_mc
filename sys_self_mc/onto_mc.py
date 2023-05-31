
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
        # print((self.onto.Component.instances()))
        # a = self.onto.search_one(iri="*", type=self.onto.Component)
        # print(a)
        # print(a.get_properties())

        # print(a.is_a)  # [rm_domain.LocalizationSensor]
        # print(a.INDIRECT_is_a) # [rm_domain.LocalizationSensor, rm_domain.Sensor, owl.Thing, sys_self.ComponentHW, sys_self.Component]
        # print(self.onto.Component.descendants())
        # print()
        # a = self.onto.search_one(iri="*", type=self.onto.Component)
        # print(a)
        # for prop in a.get_properties():
        #     for value in prop[a]:
        #         print("%s.%s == %s" % (a.name, prop.python_name, value))
        self.get_adaption_requeriments()



    def get_adaption_requeriments(self):
        # application of yoneda lemma
        # decide the reconfig
        # self.perform_reasoning()
        case = 'lidar'
        adapt_candidates = []
        components = self.onto.search(iri="*", type=self.onto.Component)
        comp_case = self.onto.search_one(iri="*{}".format(case), type=self.onto.Component)
        components.remove(comp_case) # remove case component


        # check if main relationships (capability/goal) remains
        for comp in components:
                if self.onto.realizes[comp] == self.onto.realizes[comp_case]:
                    # print("Component", comp.name, "realizes capablity", self.onto.realizes[comp], "as", comp_case.name, "did.")
                    if self.onto.contributesToGoal[comp] == self.onto.contributesToGoal[comp_case]:
                        # print("Component", comp.name, "contributes to goal", self.onto.contributesToGoal[comp], "as", comp_case.name, "did.")
                        if self.check_component_status(comp) == ["AVAILABLE"]:
                            # print("Component", comp.name, "available contributing to the same goal and capability")
                            print("Component {} suitable for adaptation".format(comp.name))
                            adapt_candidates.append(comp)
                #     else:
                #         print("Component", comp.name, "not suitable, not contributes to goal", self.onto.contributesToGoal[comp])
                # else:
                #     print("Component", comp.name, "not suitable, not realizes capability", self.onto.realizes[comp])
        
        # check interfaces to decide if we need more components
        # for candidate in adapt_candidates:
        #     candidate_int = self.check_interface(candidate)
        #     comp_case_int = self.check_interface(candidate)

    def check_component_status(self, component):
        comp_status = self.onto.search_one(iri=("*{}*").format(component.name), type=self.onto.ComponentStatus)
        if comp_status != None:
            return self.onto.hasComponentStatusValue[comp_status]
        else:
            return None
        
    # def check_interface(self, component):
    #     int_candidate_indiv = self.onto.search_one(iri=("*{}*").format(component.name), type=self.onto.Interface)
    #     if int_candidate_indiv != None:
    #         return self.onto.isType[int_candidate_indiv]
    #     else:
    #         return None
    # def check_adaptor_interface(self):
    #     interface_adaptor = self.onto.search_one(iri=("*"), type=self.onto.InterfaceAdaptor)
    #     # not valid to search type interface adaptor because Interface Adaptor is rm we want a general one

    # def push_out(self):
        # detect the entities affected by a contingency AND the entities affected by a change
    
    # def change_status(self, individual, value):
    #     #TODO

path_owl = os.path.join(get_package_share_directory('sys_self_mc'), 'ontologies')
names = ["sys_self.owl","rm_domain.owl", "app_loc.owl"]
clase = SysSelf(path_owl, names)
clase.load_OWL_file()
clase.get_relations()