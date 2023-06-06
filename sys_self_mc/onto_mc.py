
from owlready2 import *
import logging
import signal, sys, os
from threading import Lock
from datetime import datetime
from ament_index_python.packages import get_package_share_directory

class SysSelf:

    def __init__(self, owl_path, owl_names):
        self.onto = None     # owl application model
        self.sysself = None # owl main model
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
    def save_ontology_exit(self):
        # self.get_logger().info("----------Saving current ontology log------------")
        # now = datetime.now()
        # formatted_date = now.strftime("%Y-%m-%d_%H-%M-%S")
        # file_str = "log_owl_" + formatted_date + ".owl"
        file_str = "log_owl.owl"
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

            self.onto = onto_partial[0] # the first ontology loaded must be sys self
            # load also domain and application ontology
            self.onto.imported_ontologies.append(onto_partial[1])
            self.onto.imported_ontologies.append(onto_partial[2])
            self.sysself = onto_partial[2] 
           
        except Exception as e:
            logging.exception("{0}".format(e))
            return None

    def receive_update(self):
        msg = "UNAVAILABLE"
        source ="lidar_status"
        type = "hasComponentStatusValue"
       
        entity = self.onto.search_one(iri="*{}".format(source))

        # update OWL
        if entity:
            if type == "hasComponentStatusValue":
                with self.ontology_lock:
                    with self.onto:
                        entity.hasComponentStatusValue.clear()
                        entity.hasComponentStatusValue.append(msg)
                self.perform_reasoning()

                print((self.onto.lidar_status.hasComponentStatusValue))
                return True
        
            elif type == "a":
                # TODO REST CASES
                pass
        else:
            return False
        
    def get_functors_category(self, entity):
        functors = []
  
        # TODO if entity is a metric - check type of metric and which main element affects

        if entity:
            for entity_class in entity.INDIRECT_is_a: # get main class of the entity
                if entity_class.name == "Component" or entity_class.name == "Value" or entity_class.name == "Goal" or  entity_class.name == "Capability":
                    break

        # functors are relationships in which the range is capability, goal, component (excluding itself type)
            for property in entity.get_properties():
                range_name = property.range[0].name
                if ((range_name == "Component" or range_name == "Value" or range_name == "Goal" or  range_name == "Capability") and range_name != entity_class.name):
                    functors.append(property)
            return (functors, entity_class)
        else:
            return (None, None)

    def get_adaption_mechanism(self):
        source ="lidar_status"
        type = source.split("_")[0]
        entity = self.onto.search_one(iri="*{}".format(type)) # lidar
        self.perform_reasoning()
        (funct, cat) = self.get_functors_category(entity)

        
        if cat.name == "Component":
            adaption = self.adaption_mechanism_component(entity, funct, cat)
        
        self.propagate_tpm(adaption, entity)
           

    def adaption_mechanism_component(self, entity, funct, cat):
        entities = self.onto.search(iri="*", type = cat) # objects in the seame category
        entities.remove(entity) # remove working element
         # search functors preserved
        for fnt in funct:
            for entity_alt in entities:
                if fnt[entity_alt] != fnt[entity]:
                    if entity_alt in entities: entities.remove(entity_alt)
                    break
        print("Alternative component found:", entities)

                # search required changes in morphisms
        entity_value = entities[0] # only supperted one alternative entity 
        morphisms = list(set(entity_value.get_properties()).symmetric_difference(set(funct))) # all the relationships not preserved in functors are morph
        adaption_msg = [None, None]
      
        for morph in morphisms:
            related_individual = morph[entity_value][0]
     
            for prop in related_individual.get_properties():
                if prop.name == "hasComponentStatusValue": # check availability

                    if "AVAILABLE" in related_individual.hasComponentStatusValue:
                        print("Component", entity_value, "AVAILABLE")
                        adaption_msg[0] = entity_value      
                    else:
                            print("Alternative component NOT AVAILABLE")

                elif prop.name == "isType": # check interface morphism between components

                    in_value_interface = related_individual.isType
                    entity_int_indiv = entity.hasInterface[0]
                    out_value_interface = entity_int_indiv.isType
                            
                    required_value_interface_in = self.onto.search_one(iri = "*in", isType = in_value_interface)
                    required_value_interface_out = self.onto.search_one(iri = "*out", isType = out_value_interface)

                    required_element = self.onto.search_one(iri = "*", hasInterfaceOut = required_value_interface_out, hasInterfaceIn = required_value_interface_in)
                    print("REQUIRES", required_element.name, "to be equivalent")
                    adaption_msg[1] = required_element

                else:
                    print("Property", prop, "not supported yet.")
        return adaption_msg


    def propagate_tpm(self, adapt, entity):
   
        new_tpms = self.onto.search(iri ="*", measuresComponentPerf = adapt[0], type=self.sysself.TechnicalPerformanceMeasure)
        old_tpms = self.onto.search(iri ="*",  measuresComponentPerf = entity, type=self.sysself.TechnicalPerformanceMeasure)
        changes = {}


        for new_tpm in new_tpms:
            for old_tpm in old_tpms:
                new_a_mop = new_tpm.affectsMetric
                old_a_mop = old_tpm.affectsMetric
                if new_a_mop == old_a_mop:
                    if new_tpm.hasMetricValue > old_tpm.hasMetricValue:
                        for new_mop in new_a_mop:
                            changes[new_mop.name] = "increased"
                    elif new_tpm.hasMetricValue < old_tpm.hasMetricValue:
                        for new_mop in new_a_mop:
                            changes[new_mop.name] = "decreased"

                
        return(changes)              
    
    # def propagate_mop():
        
    # def analize_value_changes():
    
    # def notify_stakeholder(self, value_change):
            

if __name__ == '__main__':
    path_owl = os.path.join(get_package_share_directory('sys_self_mc'), 'ontologies')
    names = ["app_loc.owl","rm_domain.owl", "sys_self.owl"]
    clase = SysSelf(path_owl, names)
    clase.load_OWL_file()
    clase.get_adaption_mechanism()
    
    clase.save_ontology_exit()