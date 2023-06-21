
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
                    self.get_logger().info("----------Reasoner executed------------")
                    return_value = True
                except Exception as err:
                    logging.exception("{0}".format(err))
                    return False
                    # raise err

        return return_value

    # For debugging purposes: saves the runtime ontology in file
    def save_ontology_exit(self, signal, frame):
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

    def check_status(self, source):
        entity = self.onto.search_one(iri="*{}".format(source))
        return entity.hasComponentStatusValue[0]


    def receive_update(self, status, source, type):
        entity = self.onto.search_one(iri="*{}".format(source))
        # update OWL
        if entity:
            if type == "hasComponentStatusValue":
                with self.ontology_lock:
                    with self.onto:
                        entity.hasComponentStatusValue.clear()
                        entity.hasComponentStatusValue.append(status)

                self.perform_reasoning()

                self.get_logger().info("OWL: Component value {} changed to {}".format(entity.name, entity.hasComponentStatusValue))
                return True
        else:
            return False
        
    def get_category(self, entity):
        if entity:
            for entity_class in entity.INDIRECT_is_a: # get main class of the entity
                if entity_class.name == "Component" or entity_class.name == "Value" or entity_class.name == "Goal" or  entity_class.name == "Capability":
                    break
            return entity_class
        else:
            return None
        
    def check_metric(self, metric, value):
        entity = self.onto.search_one(iri="*{}".format(metric), type = self.sysself.Metric)
        value = float(value)
        if value < entity.hasMetricValue[0]:
            if bool(entity.measuresReachedCapability):
                self.get_logger().info("Capability {} underachieved, searching for alternatives".format(entity.measuresReachedCapability[0]))
                return entity.measuresReachedCapability[0]
            elif bool(entity.measuresValue):
                self.get_logger().info("Value {} underachieved, no alternative found".format(entity.measuresReachedCapability[0]))
                return None
        else:
            return None



    def get_functors(self, entity, cat):
        functors = []
        # functors are relationships in which the range is capability, goal, component (excluding itself type)
        for property in entity.get_properties():
            range_name = property.range[0].name
            if ((range_name == "Component" or range_name == "Value" or range_name == "Goal" or  range_name == "Capability") and range_name != cat.name):
                functors.append(property)

        return functors
  
        
    def get_alternative_from_morphisms(self, functors, ent, cat): 

        objects = self.onto.search(iri="*", type = cat) # objects in the same category
        objects.remove(ent) # remove working element
        interface_objects = self.onto.search(iri = "*", type = (self.onto.search_one(iri = "*InterfaceAdaptor*")))
        for io in interface_objects:
            if io in objects:
                objects.remove(io) # remove interface adaptor element
    
        for obj in objects:
            morphisms = list(set(obj.get_properties()).difference(set(functors))) # all the relationships not preserved in functors are morph

            object_morph = [None, None]
            for morph in morphisms:
                if morph[obj][0] is not None: # relationship created
                    related_individual = morph[obj][0]
                    if cat.name == "Component":
                        for prop in related_individual.get_properties():
                            if prop.name == "hasComponentStatusValue": # check availability
                                if "AVAILABLE" in related_individual.hasComponentStatusValue:
                                    self.get_logger().info("Component {} AVAILABLE".format(obj))
                                    object_morph[0] = obj
                            
                            elif prop.name == "isType": # check interface morphism between components
                                in_value_interface = related_individual.isType
                                entity_int_indiv = ent.hasInterface[0]
                                out_value_interface = entity_int_indiv.isType

                                required_value_interface_in = self.onto.search_one(iri = "*in", isType = in_value_interface)
                                required_value_interface_out = self.onto.search_one(iri = "*out", isType = out_value_interface)
                                
                                required_element = self.onto.search_one(iri = "*", hasInterfaceOut = required_value_interface_out, hasInterfaceIn = required_value_interface_in)
                                self.get_logger().info("REQUIRES {} to be equivalent".format(required_element))
                                object_morph[1] = required_element

                    # TODO find all morph
                    # if cat.name == "Capability":
                    # if cat.name == "Goal":
                    # if cat.name == "Value":

            
            if None not in object_morph:
                return object_morph

        self.get_logger().info("No alternative object found in {} category".format(cat.name))
        return (None, None)            

    def deduce_morphisms_in_cat(self, diagnosed_entity, functors):
        for fnc in functors:
            object_related = fnc[diagnosed_entity][0]
            object_cat = self.get_category(object_related)
            if object_cat.name == "Component": # OTHER CASES NOT SUPPORTED YET 
                object_functors = self.get_functors(object_related, object_cat)
                adaption_component = self.get_alternative_from_morphisms(object_functors, object_related, object_cat)
                
                self.create_new_morphism(adaption_component[0], fnc, diagnosed_entity)
                return adaption_component
        return (None, None)
     
    
    def create_new_morphism(self, obj_alternative, funct, entity):
        self.get_logger().info("Creating new morphism from relation in other category")
        cat_entity = self.get_category(entity)
        possible_domain = self.onto.search(iri="*", type = cat_entity)
        possible_domain.remove(entity)
        for pd in possible_domain:
            if pd != entity and obj_alternative in funct[pd]:
                domain = pd
                break

        if cat_entity.name == "Capability":
            entity.composableWithCapability = [domain]
            self.perform_reasoning() # updated ontology
            
        # TODO other possible morph
        # if cat.name == "Goal":
        # if cat.name == "Value":

    def find_adaption(self, entity_name):
        entity = self.onto.search_one(iri="*{}".format(entity_name))
        cat = self.get_category(entity)
        functors = self.get_functors(entity, cat)
        
        obj_alternative = self.get_alternative_from_morphisms(functors, entity, cat) # search altenative in same category
        if None in obj_alternative: # deduce alternatives in other categories (from functors)
            self.get_logger().info("Searching for alternatives in other categories")
            obj_alternative = self.deduce_morphisms_in_cat(entity, functors)
            if None in obj_alternative: # no alternatives in other categories (from functors)
                self.get_logger().info("No possible alternatives, waiting for user input----------------------")
                return (None, None)
            
        # propagate changes
        changes_mop = self.propagate_tpm(obj_alternative, entity)
        self.propagate_mop(changes_mop)
        return obj_alternative
            

    def propagate_tpm(self, adapt, entity):
        new_tpms = self.onto.search(iri ="*", measuresComponentPerf = adapt[0], type=self.sysself.TechnicalPerformanceMeasure)
        old_tpms = self.onto.search(iri ="*",  measuresComponentPerf = entity, type=self.sysself.TechnicalPerformanceMeasure)
        changes_mop = {}

        for new_tpm in new_tpms:
            if bool(old_tpms): # check if old list is empty
                for old_tpm in old_tpms: # CASE when substituting components
                    new_a_mop = new_tpm.affectsMetric
                    old_a_mop = old_tpm.affectsMetric
                    if new_a_mop == old_a_mop:
                        if new_tpm.hasMetricValue > old_tpm.hasMetricValue:
                            for new_mop in new_a_mop:
                                changes_mop[new_mop] = "increased"
                        elif new_tpm.hasMetricValue < old_tpm.hasMetricValue:
                            for new_mop in new_a_mop:
                                changes_mop[new_mop] = "decreased"
            else: # CASE adding new components
                if new_tpm.hasMetricValue[0] > 0.0:
                    new_a_mop = new_tpm.affectsMetric
                    for new_mop in new_a_mop:
                        changes_mop[new_mop] = "increased"
        return changes_mop

    def propagate_mop(self, changes_mop):
        changes_value = {}

        if changes_mop:
            for mop in changes_mop.keys():
                moe_affected = mop.affectsMetric
                for moe_aff in moe_affected:
                    for value_aff in moe_aff.measuresValue:
                        if bool(moe_aff.affectsInPossitive): # if exist
                            if moe_aff.affectsInPossitive == [False]:
                                if changes_mop[mop] == "increased":
                                    changes_value[value_aff] = ("decreased", moe_aff)
                                else:
                                    changes_value[value_aff] = ("increased", moe_aff)
                        else:
                            changes_value[value_aff] = (changes_mop[mop], moe_aff)

                        if moe_aff.affectsMetric is not None: # propagation in MOE
                            for moe in moe_aff.affectsMetric:
                                if bool(moe.affectsInPossitive): # if exist
                                    if moe.affectsInPossitive == [False]:
                                        if changes_mop[mop] == "increased":
                                            changes_value[moe.measuresValue[0]] = ("decreased", moe)
                                        else:
                                            changes_value[moe.measuresValue[0]] = ("increased", moe)
                                else:
                                    changes_value[moe.measuresValue[0]] = (changes_mop[mop], moe)


        self.notify_stakeholder(changes_value)
        return changes_value

    def notify_stakeholder(self, value_change):
        for value in value_change.keys():
            stakeholders = self.onto.search(iri="*", interestedIn = value)
            for sk in stakeholders:
                self.get_logger().info("Value {} {} after adaption because change in MOE {}".format(value.name, value_change[value][0].upper(), value_change[value][1].name))
                self.get_logger().info("Main stakeholder affected: {}\n".format( sk.name))



if __name__ == '__main__':
    path_owl = os.path.join(get_package_share_directory('sys_self_mc'), 'ontologies')
    names = ["app_attach.owl","rm_domain.owl", "sys_self.owl"]
    clase = SysSelf(path_owl, names)
    clase.load_OWL_file()
    clase.perform_reasoning()
    clase.find_adaption("cap_extract")

    # names = ["app_loc.owl","rm_domain.owl", "sys_self.owl"]
    # clase = SysSelf(path_owl, names)
    # clase.load_OWL_file()
    # clase.perform_reasoning()
    # clase.find_adaption("lidar")

    clase.save_ontology_exit()