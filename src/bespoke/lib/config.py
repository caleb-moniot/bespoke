"""
.. module:: config
   :platform: Linux, Windows
   :synopsis: This module contains classes used to parse and store information from associated 
       config files used by Bespoke.
   :license: BSD, see LICENSE for more details.

.. moduleauthor:: Ryan Gard <ryan.a.gard@outlook.com>
"""
__version__ = 0.2

# ===================================================================================================
#  Imports
# ===================================================================================================
import abc
import logging
from re import compile
from lxml import etree as et
from os.path import isfile
from collections import OrderedDict, Counter
from copy import deepcopy
from hypervisor import VBoxMachine, VagrantMachine, VMError
from core import Tool, Build, TestCase, TestPlan, SystemUnderTest, CoreError


# ===================================================================================================
#  Classes
# ===================================================================================================
class _Config(object):
    """This class is the abstract base class for all config classes. It provides
    the basic parsing functionality for XSD validation.
    
    Args:
        xml_config_path (str): The path to the XML config file that contains
            information to be parsed and stored.
        _xsd_file (str)(opt): The path to the XSD file to use for XML 
            validation.
        
    Raises:
        :class:`ConfigError`: The config file or XSD file were not found.
    """
    
    __metaclass__ = abc.ABCMeta
    
    # ===============================================================================================
    #  Class Constants
    # ===============================================================================================
    # This covers both UNIX and Windows paths.
    _RGX_PATH = compile(r'^(.*?/|.*?\\)?([^\./|^\.\\]+)(?:\.([^\\]*)|)$')
    _RGX_FQDN = compile(r'(?=^.{1,254}$)(^(?:(?!\d+\.)[a-zA-Z0-9_\-]{1,63}\.?)+(?:[a-zA-Z]{2,})$)')
    _RGX_HOST = compile(r'^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$')
    _RGX_IPv4 = compile(r'^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$')
    _RGX_EMAIL = compile(r'^([\w\-\.]+)@((\[([0-9]{1,3}\.){3}[0-9]{1,3}\])|(([\w\-]+\.)+)([a-zA-Z]{2,4}))$')
    _RGX_PORT = compile(r'^(6553[0-5]|655[0-2]\d|65[0-4]\d\d|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3}|0)$')
     
    def __init__(self, xml_config_file, xsd_file=''):
        self._config_file = xml_config_file
        self._xsd_file = xsd_file
        
        # The etree documents
        self._xml_config_doc = None
        self._xsd_doc = None
        
        # The dictionary containing content.
        # Note: this could have high complexity.
        self._content = OrderedDict()
        self._config_version = 0
        
        # Test to make sure that the paths are valid.
        if not isfile(self._config_file):
            raise ConfigError('Config file not found!', self._config_file)
        
        if self._xsd_file != '' and not isfile(self._xsd_file):
            raise ConfigError('XSD file not found!', self._xsd_file)
    
    @abc.abstractmethod
    def __getitem__(self, key):
        """This method extends the container lookup of the class objects so you can access content
        items directly without resorting to the using the '_content' dictionary.
        
        Returns:
           (obj)
           
        Raises:
            KeyError: The specified key does not exist.
        """
        
        return self._content[key]
        
    @abc.abstractmethod
    def __iter__(self):
        """Provide an iterator for the internal content dictionary.
        
        Returns:
           (iterator)
           
        Raises:
            None
        """
        
        return self._content.__iter__()
    
    @abc.abstractmethod
    def load_content(self):
        """Load all the content from the config document into the object.
        Note: it is expected that the subclasses of _Config will kick this method off in the 
        __init__ method. It is not hooked up here since this is an ABC.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated
                XML Schema or config does not have valid XML formatting.
        """
        
        pass
    
    @abc.abstractmethod
    def _load_xsd(self):
        """Load the XSD document and verify that it is properly formatted.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The XSD has incorrect format.
        """
        
        try:
            self._xsd_doc = et.XMLSchema(et.parse(self._xsd_file))  #  @UndefinedVariable
        except (et.XMLSyntaxError, et.XMLSchemaParseError), e:  #  @UndefinedVariable
            raise ConfigError(e.message, self._xsd_file)
    
    @abc.abstractmethod
    def validate_config(self, suppress_exceptions=False):
        """This method will use the XSD document to validate the content of the associated config
        file.
        
        Args:
            suppress_exceptions (bool): Only return True/False and stop all exceptions from popping.
        
        Returns:
            (bool)
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated XML Schema.
        """
        
        self._load_xsd()
        
        # Make sure the XML config was parsed first.
        if self._xml_config_doc == None:
            raise ConfigError(("The config has not been parsed yet! You must run "
                        "'parse_config' before validating!"), 
                        self._config_file)
        
        if not self._xsd_doc.validate(self._xml_config_doc):
            if suppress_exceptions:
                return False
            else:
                # Get the last error and build a good error message.
                last_error = self._xsd_doc.error_log.last_error
                error_message = \
                    "{0} Line: {1} Column: {2}".format(last_error.message,
                                                       last_error.line,
                                                       last_error.column)
                
                raise ConfigError(error_message, self._config_file)
        
        return True
    
    @abc.abstractmethod
    def parse_config(self, validate=True):
        """This method will use the XSD document to validate the content of the associated config
        file.
        
        Args:
            validate (bool): Enable config validation against XSD.
        
        Returns:
            (bool)
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated
                XML Schema or config does not have valid XML formatting.
        """
        
        try:
            self._xml_config_doc = et.parse(self._config_file)  #  @UndefinedVariable
        except et.XMLSyntaxError, e:  #  @UndefinedVariable
            raise ConfigError(e.message, self._config_file)
        
        # Grab the config version.
        try:
            self._config_version = \
                int(self._xml_config_doc.getroot().attrib['version'])
        except KeyError:
            raise ConfigError(("Root element of config file is missing the mandatory "
                               "attribute 'version'!"), self._config_file)
            
        if validate:
            self.validate_config()
    
    @property
    def xml_config_file(self):
        """The XML file containing config information.
        
        Returns:
            (str): The path to the file.
        """
        
        return self._config_file
    
    @property
    def xsd_file(self):
        """The XSD file used for config validation.
        
        Returns:
            (str): The path to the file.
        """
        
        return self._xsd_file
    
    @property
    def get_content(self):
        """The content dictionary of the _Config object.
        
        Returns:
            ({str:obj}): The content dictionary.
        """
        
        return self._content
    
    def _extract_simple_text(self, content_dictionary, root_element, name, validate_content=None):
        """Extract the text from an XML element and load it into a dictionary.
        
        Args:
            content_dictionary ({str:str}): A dictionary to update with XML contents.
            root_element (etree): The root etree element that holds the child element with text.
            name (str): The name of the child etree element from which to extract text.
            validate_content (func)(opt): A function that excepts a string and returns True/False
                on whether content matches desired format.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The text content does not match the desired format!
        """
        
        element_text = root_element.find(name).text
        
        if validate_content is not None:
            if not validate_content(element_text):
                raise ConfigError('The element "{0}" with the text "{1}" has '
                                  'invalid text format!'.format(name, element_text),
                                  self.xml_config_file)
            
        content_dictionary[name] = element_text
        
    def _extract_simple_attrib(self, 
                               content_dictionary, 
                               root_element, 
                               element_name,
                               attribute_name, 
                               validate_content=None):
        """Extract the text from an XML element attribute and load it into a dictionary.
        
        Args:
            content_dictionary ({str:str}): A dictionary to update with XML contents.
            root_element (etree): The root etree element that holds the child element with text.
            element_name (str): The name of the child etree element from which to extract text.
            attribute_name (str): The name of the element attribute from which to extract text.
            validate_content (func)(opt): A function that excepts a string and returns True/False
                on whether content matches desired format.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The text content does not match the desired format!
        """
        
        attribute_text = root_element.find(element_name).attrib[attribute_name]
        
        if validate_content is not None:
            if not validate_content(attribute_text):
                raise ConfigError('The element "{0}" with the attribute "{1}" has '
                                  'invalid text format for attribute!'.format(element_name, 
                                                                              attribute_name),
                                  self.xml_config_file)
            
        content_dictionary[attribute_name] = attribute_text
        
    def _extract_list_simple_text(self, 
                                  content_dictionary, 
                                  root_element, 
                                  name, 
                                  content_key, 
                                  validate_content=None):
        """Extract text from multiple elements with the same name; pack them into a list and add
        then to a content dictionary.
        
        Args:
            content_dictionary ({str:[str]}): A dictionary to update with XML contents.
            root_element (etree): The root etree element that holds the child elements.
            name (str): The name of the child etree elements from which to extract text.
            content_key (str): The key name to store the list under in the "_content" dictionary.
            validate_content (func)(opt): A function that excepts a string and returns True/False
                on whether content matches desired format.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The text content does not match the desired format!
        """
        
        elements_list = [ete.text for ete in root_element.findall(name)]
        
        if validate_content is not None:
            for element_text in elements_list:
                if not validate_content(element_text):
                    raise ConfigError('The element "{0}" with the text "{1}" has '
                                      'invalid text format!'.format(name, element_text),
                                      self.xml_config_file)
                
        content_dictionary[content_key] = elements_list
        
    def _extract_dictionary_simple_text(self, 
                                        content_dictionary, 
                                        root_element, 
                                        name,
                                        attrib_key, 
                                        content_key, 
                                        validate_content=None):
        """Extract text from multiple elements with the same name; pack them into a dictionary and
        add then to a content dictionary.
        
        Args:
            content_dictionary ({str:[str]}): A dictionary to update with XML contents.
            root_element (etree): The root etree element that holds the child elements.
            name (str): The name of the child etree elements from which to extract text.
            attrib_key (str): The name of the XML attribute to use as the dictionary key.
            content_key (str): The key name to store the dictionary under in the "_content" 
                dictionary.
            validate_content (func)(opt): A function that excepts a string and returns True/False
                on whether content matches desired format.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The text content does not match the desired format!
        """
        
        elements_dict = {ete.attrib[attrib_key]:ete.text for ete in root_element.findall(name)}
        
        if validate_content is not None:
            for element_text in elements_dict.keys():
                if not validate_content(element_text):
                    raise ConfigError('The element "{0}" with the text "{1}" has '
                                      'invalid text format!'.format(name, element_text),
                                      self.xml_config_file)
                
        content_dictionary[content_key] = elements_dict
        
    @classmethod
    def valid_path(cls, path):
        """Verify that a string is a valid UNIX or Windows path. (Includes UNC relative paths and
        local paths with tokens i.e. %TOKEN%)
        
        Args:
            path (str) = The path string to validate.
        
        Returns:
            (bool)
        
        Raises:
            None
        """
        
        return True if cls._RGX_PATH.match(path) else False
    
    @classmethod
    def valid_ip_address(cls, address):
        """Verify that a string is a valid IPv4 address.
        
        Args:
            address (str) = The address to validate.
        
        Returns:
            (bool)
        
        Raises:
            None
        """
        
        return True if cls._RGX_IPv4.match(address) else False
    
    @classmethod
    def valid_fqdn(cls, address):
        """Verify that a string is a valid FQDN.
        
        Args:
            address (str) = The address string to validate.
        
        Returns:
            (bool)
        
        Raises:
            None
        """
        
        return True if cls._RGX_FQDN.match(address) else False
    
    @classmethod
    def valid_network_address(cls, address):
        """Verify that a string is a valid IPv4 address or FQDN.
        
        Args:
            address (str) = The address to validate.
        
        Returns:
            (bool)
        
        Raises:
            None
        """
        
        return True if (cls._RGX_IPv4.match(address) or 
                        cls._RGX_FQDN.match(address) or
                        cls._RGX_HOST.match(address)
                        ) else False
    
    @classmethod
    def valid_email(cls, email_address):
        """Verify that a string is a valid e-mail address.
        
        Args:
            email_address (str) = The e-mail address string to validate.
        
        Returns:
            (bool)
        
        Raises:
            None
        """
        
        return True if cls._RGX_EMAIL.match(email_address) else False
    
    @classmethod
    def valid_port(cls, port):
        """Verify that a string is a valid port address.
        
        Args:
            port (str) = The port string to validate.
        
        Returns:
            (bool)
        
        Raises:
            None
        """
        
        return True if cls._RGX_PORT.match(port) else False


class GlobalConfig(_Config):
    """This class will validate, parse and store information contained in the GlobalConfig file for
    Bespoke.
    
    Args:
        xml_config_file (str) = The path to the XML config file that contains information to be 
            parsed and stored.
        xsd_path (str) = The path to the XSD file to use for XML validation.
        
    Raises:
        :class:`ConfigError`: The XML config file does not conform the associated XML Schema or 
            config does not have valid XML formatting.
    """
    
    def __init__(self, xml_config_file, xsd_path):
        super(GlobalConfig, self).__init__(xml_config_file, xsd_path)

        # Instantiate logging object.
        self.logger = logging.getLogger('bespoke.config.GlobalConfig')

        self.parse_config()
        self.load_content()
        
    def load_content(self):
        """Load all the content from the config document into the object.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated
                XML Schema or config does not have valid XML formatting.
        """
        
        # Get the root of the config.
        xml_root = self._xml_config_doc.getroot()
        
        # Populate the content dictionary.
        self._extract_simple_text(self._content,
                                  xml_root,
                                  'BespokeServerHostname',
                                  self.valid_network_address)
        self._extract_simple_text(self._content, xml_root, 'ConfigPath', self.valid_path)
        self._extract_simple_text(self._content, xml_root, 'TestRunPath', self.valid_path)
        self._extract_simple_text(self._content, xml_root, 'TestPlanPath', self.valid_path)
        self._extract_simple_text(self._content, xml_root, 'TestScriptPath', self.valid_path)
        self._extract_simple_text(self._content, xml_root, 'ToolPath', self.valid_path)
        self._extract_simple_text(self._content, xml_root, 'ResultsPath', self.valid_path)
        self._extract_simple_text(self._content, xml_root, 'ResultsURL', self.valid_path)
        self._extract_simple_text(self._content, xml_root, 'GlobalLog', self.valid_path)
        self._extract_list_simple_text(self._content, 
                                       xml_root.find('ResourceConfigs'), 
                                       'ResourceConfig', 
                                       'ResourceConfigs',
                                       self.valid_path)
    
    def _load_xsd(self):
        """Load the XSD document and verify that it is proper
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The XSD has incorrect format.
        """
        
        super(GlobalConfig, self)._load_xsd()
        
    def validate_config(self, suppress_exceptions=False):
        """This method will use the XSD document to validate the content of the associated config
        file.
        
        Args:
            suppress_exceptions (bool): Only return True/False and stop all exceptions from popping.
        
        Returns:
            (bool)
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated XML Schema.
        """
        
        super(GlobalConfig, self).validate_config(suppress_exceptions)
        
    def parse_config(self, validate=True):
        """This method will use the XSD document to validate the content of the associated config
        file.
        
        Args:
            validate (bool): Enable config validation against XSD.
        
        Returns:
            (bool)
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated
                XML Schema or config does not have valid XML formatting.
        """
        
        super(GlobalConfig, self).parse_config(validate)
        
    def __getitem__(self, key):
        """This method extends the container lookup of the class objects so you can access content
        items directly without resorting to the using the '_content' dictionary.
        
        Returns:
           (obj)
           
        Raises:
            KeyError: The specified key does not exist.
        """
        
        return super(GlobalConfig, self).__getitem__(key)
    
    def __iter__(self):
        """Provide an iterator for the internal '_content' dictionary.
        
        Returns:
           (iterator)
           
        Raises:
            None
        """
        
        return super(GlobalConfig, self).__iter__()


class ToolConfig(_Config):
    """This class will validate, parse and store information contained in the ToolConfig.
    
    Args:
        xml_config_path (str) = The path to the XML config file that contains information to be 
            parsed and stored.
        xsd_path (str) = The path to the XSD file to use for XML validation.
        instrument_type (str) = A label for differentiating between a "Tool" config and "Build" 
            config.
        
    Raises:
        :class:`ConfigError`: The XML config file does not conform the associated XML Schema or 
            config does not have valid XML formatting.
    """
    
    def __init__(self, xml_config_path, xsd_path, instrument_type):
        super(ToolConfig, self).__init__(xml_config_path, xsd_path)

        # Instantiate logging object.
        self.logger = logging.getLogger('bespoke.config.ToolConfig')

        # Since builds and tools are the same we need to differentiate them by name.
        # This will allow for accurate exception messages.
        self._instrument_type = instrument_type
        
        self.parse_config()
        self.load_content()
        
    def load_content(self):
        """Load all the content from the config document into the object.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated
                XML Schema or config does not have valid XML formatting.
        """
        
        # Get the root of the config.
        xml_root = self._xml_config_doc.getroot()
        
        # Get all the 'Tool' etree elements.
        xml_instruments = xml_root.findall(self._instrument_type)
        
        self._process_instruments(xml_instruments, self._content)
        
    def _process_instruments(self, instruments, content):
        """Create the instrument objects from the array of etree elements.
        
        Args:
            instruments ([etree]) = A list of etree elements representing instruments from the 
                config.
            content ({str::class:`bespoke.core.Tool`}) = A dictionary to add the instruments to.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: Duplicate instruments exist. The source/install properties are 
                invalid according to type.
        """
        
        for xml_instrument in instruments:
            instrument_name = xml_instrument.find('Name').text
            instrument_version = xml_instrument.find('Version').text
            instrument_os_type = xml_instrument.find('TargetOS').text
            instrument_os_arch = xml_instrument.find('TargetOS').attrib['arch_type']
            
            # Get the sub-elements of the tool.
            xml_source = xml_instrument.find('Source')
            xml_install_method = xml_instrument.find('InstallMethod')
            
            if instrument_name in content:
                raise ConfigError(("Duplicate {0} name '{1}' specified, {0} names must be "
                                   "unique!".format(self._instrument_type, 
                                                    instrument_name)), 
                                  self._config_file)
            
            source_type = xml_source.attrib['type']
            source_copy_once = \
                True if xml_source.attrib['copy_once'].lower() in ["true", "1"] else False
            install_method_type = xml_install_method.attrib['type']
            
            try:
                source_properties = self._get_properties(source_type, xml_source)
            except ConfigError, e:
                raise ConfigError(("The {0} '{1}' has an error in the Source element: "
                                   "{2}".format(self._instrument_type, instrument_name, e.msg)), 
                                  self._config_file)
            
            try:
                install_properties = self._get_properties(install_method_type, 
                                                          xml_install_method)
            except ConfigError, e:
                raise ConfigError(("The {0} '{1}' has an error in the InstallMethod element: "
                                   "{2}".format(self._instrument_type, instrument_name, e.msg)), 
                                  self._config_file)
                
            # Add the Tool to the content dictionary.
            if self._instrument_type == 'Tool':
                content[instrument_name] = Tool(instrument_name, 
                                                instrument_os_type,
                                                instrument_os_arch,
                                                instrument_version, 
                                                source_type, 
                                                source_copy_once, 
                                                install_method_type, 
                                                source_properties, 
                                                install_properties)
            elif self._instrument_type == 'Build':
                content[instrument_name] = Build(instrument_name, 
                                                 instrument_os_type,
                                                 instrument_os_arch,
                                                 instrument_version, 
                                                 source_type, 
                                                 source_copy_once, 
                                                 install_method_type, 
                                                 source_properties, 
                                                 install_properties)
            else:
                raise ConfigError(("The {0} '{1}' has an error in the InstallMethod element: "
                                   "{2}".format(self._instrument_type, instrument_name, e.msg)), 
                                  self._config_file)
            
    def _get_properties(self, prop_type, xml_element):
        """Get property child elements from a root element.
        
        Args:
            prop_type (str) = The type of the property.
            xml_element (etree) = An XML etree element.
            
        Returns:
            ({str:str})
        
        Raises:
            None.
        """
        
        properties = {}
        xml_properties = xml_element.findall('Property')
        
        for xml_property in xml_properties:
            # If the  property text is empty make sure to convert the "None" to an empty string.
            properties[xml_property.attrib['name']] = \
                xml_property.text if xml_property.text is not None else ''
        
        self._validate_type(prop_type, properties)
        
        return properties
    
    def _validate_type(self, prop_type, properties):
        """Verify that the source/install prop_type for the tool is formatted correctly.
        
        Args:
            prop_type (str) = The prop_type of the property.
            properties (dic(str)) = A dictionary holding the properties to verify.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The specified prop_type has incorrect properties.
        """
        
        if prop_type == 'no_copy':
            self._valid_no_copy(properties)
        elif prop_type == 'basic_copy':
            self._valid_basic_copy(properties)
        elif prop_type == 'ftp_copy':
            self._valid_ftp_copy(properties)
        elif prop_type == 'http_copy':
            self._valid_http_copy(properties)
        elif prop_type == 'no_install':
            self._valid_no_install(properties)
        elif prop_type == 'basic_install':
            self._valid_basic_install(properties)
        elif prop_type == 'msi_install':
            self._valid_msi_install(properties)
        else:
            raise ConfigError(("type '{0}' is missing the is not a valid source//install type!"
                               ).format(prop_type), self._config_file)
            
    def _valid_no_copy(self, properties):
        """Verify that the properties for the 'no_copy' type are formatted correctly.
        
        Args:
            prop_type (str) = The prop_type of the property.
            properties ({str:str}) = A dictionary holding the properties to verify.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The specified type has incorrect properties.
        """
        
        if not len(properties) == 0:
            raise ConfigError("type 'no_copy' cannot have properties!")
        
    def _valid_basic_copy(self, properties):
        """Verify that the properties for the 'basic_copy' type are formatted correctly.
        
        Args:
            properties ({str:str}) = A dictionary holding the properties to verify.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The specified type has incorrect properties.
        """
        
        if not 'source_path' in properties.keys():
            raise ConfigError("type 'basic_copy' is missing the 'source_path' property!")
        elif not 'target_path' in properties.keys():
            raise ConfigError("type 'basic_copy' is missing the 'target_path' property!")
        elif not self.valid_path(properties['source_path']):
            raise ConfigError("type 'basic_copy' has a bad path for the 'source_path' property!")
        elif not self.valid_path(properties['target_path']):
            raise ConfigError("type 'basic_copy' has a bad path for the 'target_path' property!")
    
    # TODO: Unhooked, future release it may be implemented.
    def _valid_cifs_copy(self, properties):
        """Verify that the properties for the 'cifs_copy' type are formatted correctly.
        
        Args:
            properties ({str:str}) = A dictionary holding the properties to verify.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The specified type has incorrect properties.
        """
        
        if not 'source_server' in properties.keys():
            raise ConfigError("type 'cifs_copy' is missing the 'source_server' property!")
        elif not 'source_server_user' in properties.keys():
            raise ConfigError("type 'cifs_copy' is missing the 'source_server_user' property!")
        elif not 'source_server_password' in properties.keys():
            raise ConfigError("type 'cifs_copy' is missing the 'source_server_password' property!")
        elif not 'source_path' in properties.keys():
            raise ConfigError("type 'cifs_copy' is missing the 'source_path' property!")
        elif not 'target_path' in properties.keys():
            raise ConfigError("type 'cifs_copy' is missing the 'target_path' property!")
        
    def _valid_ftp_copy(self, properties):
        """Verify that the properties for the 'ftp_copy' type are formatted correctly.
        
        Args:
            properties ({str:str}) = A dictionary holding the properties to verify.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The specified type has incorrect properties.
        """
        
        if not 'source_server' in properties.keys():
            raise ConfigError("type 'ftp_copy' is missing the 'source_server' property!", 
                              self.xml_config_file)
        elif not 'source_server_port' in properties.keys():
            raise ConfigError("type 'ftp_copy' is missing the 'source_server_port' property!", 
                              self.xml_config_file)
        elif not 'source_server_user' in properties.keys():
            raise ConfigError("type 'ftp_copy' is missing the 'source_server_user' property!", 
                              self.xml_config_file)
        elif not 'source_server_password' in properties.keys():
            raise ConfigError("type 'ftp_copy' is missing the 'source_server_password' property!", 
                              self.xml_config_file)
        elif not 'source_path' in properties.keys():
            raise ConfigError("type 'ftp_copy' is missing the 'source_path' property!", 
                              self.xml_config_file)
        elif not 'target_path' in properties.keys():
            raise ConfigError("type 'ftp_copy' is missing the 'target_path' property!", 
                              self.xml_config_file)
        elif not self.valid_network_address(properties['source_server']):
            raise ConfigError("type 'ftp_copy' has a bad FQDN//IPv4 address for the "
                              "'source_server' property!")
        elif not self.valid_port(properties['source_server_port']):
            raise ConfigError("type 'ftp_copy' has a bad port number for the "
                              "'source_server_port' property!")
        elif not self.valid_path(properties['source_path']):
            raise ConfigError("type 'ftp_copy' has a bad path for the 'source_path' property!")
        elif not self.valid_path(properties['target_path']):
            raise ConfigError("type 'ftp_copy.' has a bad path for the 'target_path' property!")
            
    def _valid_http_copy(self, properties):
        """Verify that the properties for the 'http_copy' type are formatted correctly.
        
        Args:
            properties ({str:str}) = A dictionary holding the properties to verify.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The specified type has incorrect properties.
        """
        
        if not 'source_server' in properties.keys():
            raise ConfigError("type 'http_copy' is missing the 'source_server' property!")
        elif not 'source_server_port' in properties.keys():
            raise ConfigError("type 'http_copy' is missing the 'source_server_port' property!")
        elif not 'source_server_user' in properties.keys():
            raise ConfigError("type 'http_copy' is missing the 'source_server_user' property!")
        elif not 'source_server_password' in properties.keys():
            raise ConfigError("type 'http_copy' is missing the 'source_server_password' property!")
        elif not 'source_path' in properties.keys():
            raise ConfigError("type 'http_copy' is missing the 'source_path' property!")
        elif not 'target_path' in properties.keys():
            raise ConfigError("type 'http_copy' is missing the 'target_path' property!")
        elif not self.valid_network_address(properties['source_server']):
            raise ConfigError("type 'http_copy' has a bad FQDN//IPv4 address for the "
                              "'source_server' property!")
        elif not self.valid_port(properties['source_server_port']):
            raise ConfigError("type 'http_copy' has a bad port number for the "
                              "'source_server_port' property!")
        elif not self.valid_path(properties['source_path']):
            raise ConfigError("type 'http_copy' has a bad path for the 'source_path' property!")
        elif not self.valid_path(properties['target_path']):
            raise ConfigError("type 'http_copy' has a bad path for the 'target_path' property!")
           
    def _valid_no_install(self, properties):
        """Verify that the properties for the 'no_install' type are formatted correctly.
        
        Args:
            prop_type (str) = The prop_type of the property.
            properties ({str:str}) = A dictionary holding the properties to verify.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The specified type has incorrect properties.
        """
        
        if not len(properties) == 0:
            raise ConfigError("type 'no_install' cannot have properties!")
        
    def _valid_basic_install(self, properties):
        """Verify that the properties for the 'basic_install' type are formatted correctly.
        
        Args:
            properties ({str:str}) = A dictionary holding the properties to verify.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The specified type has incorrect properties.
        """
        
        if not 'source_path' in properties.keys():
            raise ConfigError("type 'basic_install' is missing the 'source_path' property!")
        elif not 'target_path' in properties.keys():
            raise ConfigError("type 'basic_install' is missing the 'target_path' property!")
        elif not self.valid_path(properties['source_path']):
            raise ConfigError("type 'basic_install' has a bad path for the 'source_path' property!")
        elif not self.valid_path(properties['target_path']):
            raise ConfigError("type 'basic_install' has a bad path for the 'target_path' property!")
        
    def _valid_msi_install(self, properties):
        """Verify that the properties for the 'msi_install' type are formatted correctly.
        
        Args:
            properties ({str:str}) = A dictionary holding the properties to verify.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The specified type has incorrect properties.
        """
        
        if not 'source_file' in properties.keys():
            raise ConfigError("type 'msi_install' is missing the 'source_file' property!")
        elif not self.valid_path(properties['source_file']):
            raise ConfigError("type 'msi_install' has a bad path for the 'source_file' property!")
    
    def _load_xsd(self):
        """Load the XSD document and verify that it is proper
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The XSD has incorrect format.
        """
        
        super(ToolConfig, self)._load_xsd()
        
    def validate_config(self, suppress_exceptions=False):
        """This method will use the XSD document to validate the content of the associated config
        file.
        
        Args:
            suppress_exceptions (bool): Only return True/False and stop all exceptions from popping.
        
        Returns:
            (bool)
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated XML Schema.
        """
        
        super(ToolConfig, self).validate_config(suppress_exceptions)
    
    def parse_config(self, validate=True):
        """This method will use the XSD document to validate the content of the associated config
        file.
        
        Args:
            validate (bool): Enable config validation against XSD.
        
        Returns:
            (bool)
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated
                XML Schema or config does not have valid XML formatting.
        """
        
        super(ToolConfig, self).parse_config(validate)
    
    def __getitem__(self, key):
        """This method extends the container lookup of the class objects so you can access content
        items directly without resorting to the using the '_content' dictionary.
        
        Returns:
           (obj)
           
        Raises:
            KeyError: The specified key does not exist.
        """
        
        return super(ToolConfig, self).__getitem__(key)
    
    def __iter__(self):
        """Provide an iterator for the internal '_content' dictionary.
        
        Returns:
           (iterator)
           
        Raises:
            None
        """
        
        return super(ToolConfig, self).__iter__()


class BuildConfig(ToolConfig):
    """This class will validate, parse and store information contained in the BuildConfig.
    
    Args:
        xml_config_path (str) = The path to the XML config file that contains information to be 
            parsed and stored.
        xsd_path (str) = The path to the XSD file to use for XML validation.
        instrument_type (str) = A label for differianting between a "Tool" config and "Build" 
            config.
        
    Raises:
        :class:`ConfigError`: The XML config file does not conform the associated XML Schema or 
            config does not have valid XML formatting.
    """
    
    def __init__(self, xml_config_path, xsd_path, instrument_type):
        super(BuildConfig, self).__init__(xml_config_path, xsd_path, instrument_type)

        # Instantiate logging object.
        self.logger = logging.getLogger('bespoke.config.BuildConfig')


class ResourceConfig(_Config):
    """This class will validate, parse and store information contained in the ResourceConfig file
    for Bespoke.
    
    Args:
        xml_config_path (str) = The path to the XML config file that contains information to be 
            parsed and stored.
        xsd_path (str) = The path to the XSD file to use for XML validation.
        
    Raises:
        :class:`ConfigError`: The XML config file does not conform the associated XML Schema or 
            config does not have valid XML formatting.
    """
    
    def __init__(self, xml_config_path, xsd_path):
        super(ResourceConfig, self).__init__(xml_config_path, xsd_path)

        # Instantiate logging object.
        self.logger = logging.getLogger('bespoke.config.ResourceConfig')

        self.parse_config()
        self.load_content()
        
    def load_content(self):
        """Load all the content from the config document into the object.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated
                XML Schema, config does not have valid XML formatting or duplicate aliases found
                for multiple resources.
        """
        
        # Get the root of the config.
        xml_root = self._xml_config_doc.getroot()
        
        # Get all the 'VirtualMachineTemplateHost' etree elements.
        xml_vm_template_hosts = xml_root.findall('VirtualMachineTemplateHost')
        
        # Get all the 'VirtualMachineHost' etree elements.
        xml_vm_hosts = xml_root.findall('VirtualMachineHost')
        
        # Get all aliases for all resource types.
        xml_aliases = xml_root.findall('.//Alias')
        
        # Verify that no duplicate alias exist for all resources.
        self._duplicate_alias_check(xml_aliases)
        
        # Create the SystemUnderTest Template objects
        for xml_vm_template_host in xml_vm_template_hosts:
            self._process_vm_template_host(xml_vm_template_host)
            
        # Create the SystemUnderTest objects
        for xml_vm_host in xml_vm_hosts:
            self._process_vm_host(xml_vm_host)
        
    def _duplicate_alias_check(self, xml_aliases):
        """Verify that no duplicate aliases exist for any resource type.
        
        Args:
            xml_aliases ([etree]) = An list of etree elements with the tag "Alias".
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: Duplicate alias was used for more than one resource.
        """
        
        alias_occurence = Counter([element.text for element in xml_aliases])
        
        for (alias, count) in alias_occurence.items():
            if count > 1:
                raise ConfigError("The resource alias '{0}' used more than once!".format(alias), 
                                  self._config_file)
            
    def _process_vm_template_host(self, vm_template_host):
        """Process all the virtual machine templates defined in the 'VirtualMachineTemplateHost'
        etree element.
        
        Args:
            vm_template_host (etree) = An etree element representing the 'irtualMachineTemplateHost 
            element that contains the SystemUnderTest template definitions on that host.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: Invalid host address.
        """
        
        provider = vm_template_host.attrib['provider']
        host = vm_template_host.attrib['host']
        
        if not ResourceConfig.valid_network_address(host):
            raise ConfigError("The host address '{0}' is not valid!".format(host), 
                        self._config_file)
        
        for xml_vm_template in vm_template_host:    
            self._process_vm_tempalte(xml_vm_template, host, provider)
    
    def _process_vm_host(self, vm_host):
        """Process all the virtual machines defined in the 'VirtualMachineHost' etree element.
        
        Args:
            vm_host (etree) = An etree element representing the 'VitualMachineHost' element that 
                contains the SystemUnderTest definitions on that host.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: Invalid host address.
        """
        
        hypervisor = vm_host.attrib['hypervisor'] 
        host = vm_host.attrib['host']
        
        if not ResourceConfig.valid_network_address(host):
            raise ConfigError("The host address '{0}' is not valid!".format(host), 
                        self._config_file)
        
        for xml_vm in vm_host:    
            self._process_vm(xml_vm, host, hypervisor)
    
    def _process_vm_tempalte(self, vm_template, host, provider):
        """Process a VM template etree element.
        
        Args:
            vm_template (etree) = The VM template etree object to process.
            host (str) = The host of the VM.
            provider (str) = The hypervisor provider of the VM template host.
        
        Returns:
            None.
        
        Raises:
            None.
        """
        
        actual_content = {'Host':host, 'Provider':provider}
        
        # Populate the content dictionary.
        self._extract_simple_text(actual_content, vm_template, 'Alias')
        self._extract_simple_text(actual_content, vm_template, 'Name')
        self._extract_simple_text(actual_content, vm_template, 'BespokeRoot', self.valid_path)
        self._extract_simple_text(actual_content, vm_template, 'UserName')
        self._extract_simple_text(actual_content, vm_template, 'Password')
        self._extract_simple_text(actual_content, vm_template, 'OSType')
        self._extract_simple_attrib(actual_content, vm_template, 'OSType', 'arch_type')
        self._extract_simple_text(actual_content, vm_template, 'OSLabel')
        self._extract_simple_text(actual_content, vm_template, 'Role')
        self._extract_list_simple_text(actual_content, vm_template.find('Tools'), 'Tool', 'Tools')
        self._extract_dictionary_simple_text(actual_content, 
                                             vm_template.find('ExtendedConfiguration'), 
                                             'Config', 
                                             'name', 
                                             'ExtendedConfiguration')
        
        # The following information is not used by VM templates so set them to None.
        actual_content['NetworkAddress'] = None
        actual_content['CheckPoints'] = None
        
        # Validate required ExtendedConfiguration information for the template.
        self._process_extended_config(actual_content)
        
        # Add a _VirtualMachine.
        self._add_virtual_template(actual_content)
        
        # Finally add the a SUT to the ResourceConfig content.
        self._add_sut_to_content(actual_content, 'template')
        
    def _process_vm(self, vm, host, hypervisor):
        """Process a VM etree element.
        
        Args:
            vm (etree) = The VM etree object to process.
            host (str) = The host of the VM.
            hypervisor (str) = The hypervisor of the VM host.
        
        Returns:
            None.
        
        Raises:
            None.
        """
        
        actual_content = {'Host':host, 'HyperVisor':hypervisor}
        
        # Populate the content dictionary.
        self._extract_simple_text(actual_content, vm, 'Alias')
        self._extract_simple_text(actual_content, vm, 'Name')
        self._extract_simple_text(actual_content, vm, 'NetworkAddress', self.valid_network_address)
        self._extract_simple_text(actual_content, vm, 'BespokeRoot', self.valid_path)
        self._extract_simple_text(actual_content, vm, 'UserName')
        self._extract_simple_text(actual_content, vm, 'Password')
        self._extract_simple_text(actual_content, vm, 'OSType')
        self._extract_simple_attrib(actual_content, vm, 'OSType', 'arch_type')
        self._extract_simple_text(actual_content, vm, 'OSLabel')
        self._extract_simple_text(actual_content, vm, 'Role')
        self._extract_list_simple_text(actual_content, vm.find('Tools'), 'Tool', 'Tools')
        
        # Checkpoints are a special case so deal with them separately.
        self._process_checkpoints(vm, actual_content)
        
        # Add a _VirtualMachine.
        self._add_virtual_machine(actual_content)
        
        # Finally add the a SUT to the ResourceConfig content.
        self._add_sut_to_content(actual_content, 'static')
    
    def _add_virtual_template(self, content):
        """Add a _VirtualMachine object to the content for a templated virtual machine.
        
        Args:
            content ({str:obj}) = A dictionary holding the information necessary to create a 
                SystemUnderTest object.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`= Failed to initialization the virtual machine from a template.
        """
        
        try:
            content['Machine'] = VagrantMachine(content['Host'], 
                                                content['Name'], 
                                                content['VagrantBoxURL'],
                                                content['VagrantHypervisor'],
                                                content['VagrantBoxRoot'],
                                                content['VagrantFile'])
        except VMError as e:
            raise ConfigError('Failed to initialize "{0}" virtual template machine! Reason: '
                              '{1}'.format(content['Alias'], e.msg), self.xml_config_file)

            
    def _add_virtual_machine(self, content):
        """Add a _VirtualMachine object to the content for a static virtual machine.
        
        Args:
            content ({str:obj}) = A dictionary holding the information necessary to create a 
                SystemUnderTest object.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`= Invalid hypervisor specified or failed initialization of 
                virtual machine.
        """
        
        # Create and add _VirtualMacine object to content.
        # TODO: We neeed to support the potential of credentials for VBox host.
        if content['HyperVisor'] == 'VirtualBox':
            try:
                content['Machine'] = VBoxMachine(content['Host'], content['Name'])
            except VMError as e:
                raise ConfigError('Failed to initialize "{0}" virtual machine! Reason: '
                                  '{1}'.format(content['Alias'], e.msg), self.xml_config_file)
        else:
            raise ConfigError('The hypervisor "{0}" specifice for the virtual machine "{1}" is ' 
                              'invalid!'.format(content['HyperVisor'], 
                                                content['Alias']),
                                                self.xml_config_file)
            
    def _add_sut_to_content(self, content, machine_type):
        """Add the SystemUnderTest object to the ResourceConfig content.
        
        Args:
            content ({str:obj}) = A dictionary holding the information necessary to 
                create a SystemUnderTest object.
            machine_type (str) = The machine type. ('static', 'template')
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`= Duplicate SystemUnderTest alias was used for multiple VMs.
        """
        
        # Create a SystemUnderTest and add it to the underlying content for this ResourceConfig.
        self._content[content['Alias']] = \
            SystemUnderTest(alias = content['Alias'], 
                            machine = content['Machine'], 
                            bespoke_root = content['BespokeRoot'],
                            credentials = {content['UserName']:content['Password']},
                            machine_type = machine_type,
                            network_address = content['NetworkAddress'],
                            os = content['OSType'],
                            os_label = content['OSLabel'],
                            arch_type = content['arch_type'],
                            role = content['Role'],
                            check_points = content['CheckPoints'],
                            tools = content['Tools'])
    
    def _process_checkpoints(self, vm, content):
        """Process a SystemUnderTest etree element.
        
        Args:
            vm (etree) = The VM etree object to process.
            content ({str:str}) = A dictionary holding the information necessary to 
                create a SystemUnderTest object.
        
        Returns:
            None.
        
        Raises:
            None.
        """
        
        checkpoints = content['CheckPoints'] = {}
        
        for checkpoint in vm.findall('.//CheckPoint'):
            checkpoints[checkpoint.attrib['name']] = \
                [tool.text for tool in checkpoint.findall('Tool')]
                
    def _process_extended_config(self, content):
        """Process the required "ExtendedConfig" elements exist for the given template provider.
        
        Args:
            content ({str:obj}) = A dictionary holding the information necessary to create a 
                SystemUnderTest object.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`= Invalid provider specified missing extended config 
                information.
        """
        
        # Create and add _VirtualMacine object to content.
        if content['Provider'] == 'Vagrant':
            # A list of expected extended configuration elements.
            vagrant_config_elements = ['VagrantFile', 
                                       'VagrantBoxURL', 
                                       'VagrantBoxRoot', 
                                       'VagrantHypervisor']
            
            # Verify that we have the extended configuration information needed for Vargrant.
            for vagrant_config in vagrant_config_elements:
                if vagrant_config not in content['ExtendedConfiguration'].keys():
                    raise ConfigError('The extended config element "{0}" is required for the '
                                      'Vagrant template "{1}"!'.format(vagrant_config, 
                                                                    content['Alias']),
                                                                    self.xml_config_file)
        else:
            raise ConfigError('The provider "{0}" specificed for the virtual template "{1}" is '
                              'invalid!'.format(content['Provider'], 
                                                content['Alias']),
                                                self.xml_config_file)
            
    def _load_xsd(self):
        """Load the XSD document and verify that it is proper
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The XSD has incorrect format.
        """
        
        super(ResourceConfig, self)._load_xsd()
        
    def validate_config(self, suppress_exceptions=False):
        """This method will use the XSD document to validate the content of the associated config
        file.
        
        Args:
            suppress_exceptions (bool): Only return True/False and stop all exceptions from popping.
        
        Returns:
            (bool)
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated XML Schema.
        """
        
        super(ResourceConfig, self).validate_config(suppress_exceptions)
    
    def parse_config(self, validate=True):
        """This method will use the XSD document to validate the content of the associated config
        file.
        
        Args:
            validate (bool): Enable config validation against XSD.
        
        Returns:
            (bool)
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated
                XML Schema or config does not have valid XML formatting.
        """
        
        super(ResourceConfig, self).parse_config(validate)
    
    def __getitem__(self, key):
        """This method extends the container lookup of the class objects so you can access content
        items directly without resorting to the using the '_content' dictionary. 
        
        Note:
        
        If the SUT is of the type 'template' then we send a copy back. This is necessary because
        templates can be destroyed so we don't want to send a reference to the original.
        
        Returns:
           (obj)
           
        Raises:
            KeyError: The specified key does not exist.
        """
        
        sut = self._content[key]
        
        if sut._machine_type == 'template':
            sut = deepcopy(sut)
            
        return sut
    
    def __iter__(self):
        """Provide an iterator for the internal '_content' dictionary.
        
        Returns:
           (iterator)
           
        Raises:
            None
        """
        
        return super(ResourceConfig, self).__iter__()


class TestPlanConfig(_Config):
    """This class will validate, parse and store information contained in test plan files for
    Bespoke. This is the main constructor to use for building a "TestRun".
    
    Args:
        xml_config_path (str): The path to the XML config file that contains information to be 
            parsed and stored.
        xsd_path (str) = The path to the XSD file to use for XML validation.
        available_builds ({str::class:`Tool`}) = A dictionary of available builds.
            plan.
        available_tools ({str::class:`Tool`}) = A dictionary of available tools.
            plan.
        available_resources ({str::class:`SystemUnderTest`) = A dictionary of available SUTs based 
            on Alias name.
        
    Raises:
        :class:`ConfigError`: The XML config file does not conform the associated XML Schema or 
            config does not have valid XML formatting.
    """
    
    def __init__(self, 
                 xml_config_path, 
                 xsd_path, 
                 available_builds, 
                 available_tools, 
                 available_resources):
        
        super(TestPlanConfig, self).__init__(xml_config_path, xsd_path)

        # Instantiate logging object.
        self.logger = logging.getLogger('bespoke.config.TestPlanConfig')

        # Override internal content dictionary.
        self._content = TestPlan()
        
        self._available_builds = available_builds
        self._available_tools = available_tools
        self._available_resources = available_resources
        
        self.parse_config()
        self.load_content()
        
    def load_content(self):
        """Load all the content from the config document into the object.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated
                XML Schema or config does not have valid XML formatting.
        """
        
        # Get the root of the config.
        xml_root = self._xml_config_doc.getroot()
    
        self._content.name = xml_root.attrib['name']
        
        # Get all the 'TestCase' etree elements.
        xml_test_cases = xml_root.findall("TestCase")
        
        self._process_test_cases(xml_test_cases)
        
    def _get_builds(self, test_case, xml_builds):
        """Get all the builds associated with a TestPrep.
        
        Args:
            test_case (:class:`TestCase`) = The parent test case for the builds.
            xml_builds ([etree]) = A list of etree elements that represent "Tool" objects.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: Duplicate build names exist in TestCase.
        """
        
        test_prep_builds = []
        build_occurence = Counter([element.text for element in xml_builds])
        
        for (build_name, count) in build_occurence.items():
            if count > 1:
                raise ConfigError('The build "{0}" used more than once in the "{1}" test '
                                  'case!'.format(build_name, test_case.name), self._config_file)
                
            if build_name not in self._available_builds.keys():
                raise ConfigError('The build "{0}" specified in the "{1}" test case not defined in '
                                  'any BuildConfig!'.format(build_name, test_case.name), 
                                  self._config_file)
            
            test_prep_builds.append(self._available_builds[build_name])
        
        return test_prep_builds
    
    def _get_tools(self, test_case, xml_tools):
        """Get all the tools associated with a TestPrep.
        
        Args:
            test_case (:class:`TestCase`) = The parent test case for the builds.
            xml_tools ([etree]) = A list of etree elements that represent "Tool" objects.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: Duplicate build names exist in TestCase.
        """
        
        test_prep_tools = []
        tool_occurence = Counter([element.text for element in xml_tools])
        
        for (tool_name, count) in tool_occurence.items():
            if count > 1:
                raise ConfigError('The tool "{0}" used more than once in the "{1}" test '
                                  'case!'.format(tool_name, test_case.name), self._config_file)
                
            if tool_name not in self._available_tools:
                raise ConfigError('The tool "{0}" specified in the "{1}" test case not defined in '
                                  'any ToolConfig!'.format(tool_name, test_case.name), 
                                  self._config_file)
            
            test_prep_tools.append(self._available_tools[tool_name])
        
        return test_prep_tools
            
    def _process_resource_refresh(self, test_case, xml_refresh):
        """Process the "RefreshResource" element in the test case.
        
        Args:
            test_case (:class:`TestCase`) = Add "TestPrep" objects to this test case.
            xml_refresh (etree) = An etree element with the tag "RefreshResource".
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The "RefreshResource" was invalid in some way.
        """
        
        resource_id = xml_refresh.find("ResourceID").text
        restart = True if xml_refresh.find("RestartComputer").text.lower() in ["true", "1"] \
            else False
        restart_wait = True if xml_refresh.find("RestartComputer").attrib['wait'].lower() \
            in ["true", "1"] else False
            
        try:
            test_case.add_resoure_refresh(resource_id, restart, restart_wait)
        except CoreError as e:
            raise ConfigError(e.msg, self._config_file)
        
    def _process_step(self, test_case, xml_step):
        """Process the "Step" element in the test case.
        
        Args:
            test_case (:class:`TestCase`) = Add "TestPrep" objects to this test case.
            xml_step (etree) = An etree element with the tag "Step".
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The Step was invalid in some way.
        """
        
        description = xml_step.find("Description").text
        resource_id = xml_step.find("ResourceID").text
        directory = xml_step.find("Directory").text
        interpreter = xml_step.find("Interpreter").text
        executable = xml_step.find("Executable").text
        post_wait = int(xml_step.find("PostWait").text)
        timeout = int(xml_step.find("TimeOut").text)
        restart = True if xml_step.find("RestartComputer").text.lower() in ["true", "1"] \
            else False
        restart_wait = True if xml_step.find("RestartComputer").attrib['wait'].lower() \
            in ["true", "1"] else False
        
        # We need to slash-quote (escape) the param strings because of STAF.
        params = {p.attrib['name']:r'"\"{0}\""'.format(p.text) for p in xml_step.findall('.//Param')}

        try:
            test_case.add_test_step(description, 
                                    resource_id, 
                                    directory,
                                    interpreter,
                                    executable,
                                    params,
                                    timeout, 
                                    post_wait, 
                                    restart, 
                                    restart_wait)
        except CoreError as e:
            raise ConfigError(e.msg, self._config_file)
    
    def _process_test_preps(self, test_case, xml_test_preps):
        """Process all the "PrepareVirtualMachine" elements in the test case.
        
        Args:
            test_case (:class:`TestCase`) = Add "TestPrep" objects to this test case.
            xml_test_preps ([etree]) = A list of etree elements that represent "TestPrep" objects.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The TestPrep was invalid in some way.
        """
        
        for xml_test_prep in xml_test_preps:
            sut_name = xml_test_prep.find("VirtualMachine").text
            resource_id = xml_test_prep.attrib['resource_id']
            checkpoint = xml_test_prep.find("Checkpoint").text
            post_wait = int(xml_test_prep.find("PostWait").text)
            timeout = int(xml_test_prep.find("TimeOut").text)
            restart = True if xml_test_prep.find("RestartComputer").text.lower() in ["true", "1"] \
                else False
            restart_wait = True if xml_test_prep.find("RestartComputer").attrib['wait'].lower() \
                in ["true", "1"] else False
            
            try:
                sut = self._available_resources[sut_name]
            except KeyError:
                raise ConfigError('The VirtualMachine "{0}" specified in the "{1}" test case is '
                                  'not defined in any ResourceConfig!'.format(sut_name, 
                                                                              test_case.name), 
                                  self._config_file)
                
            builds = self._get_builds(test_case, xml_test_prep.findall('.//Build'))
            tools = self._get_tools(test_case, xml_test_prep.findall('.//Tool'))
            
            try:
                test_case.add_test_prep(resource_id, 
                                        sut, 
                                        checkpoint, 
                                        post_wait, 
                                        timeout,
                                        restart,
                                        restart_wait)
            except CoreError as e:
                raise ConfigError(e.msg, self._config_file)
            
            try:
                for tool in tools:
                    test_case.add_tool(sut, tool, timeout)
                    
                for build in builds:
                    test_case.add_build(sut, build, timeout)
            except CoreError as e:
                raise CoreError(e.msg)
            
    def _process_test_steps(self, test_case, xml_test_steps):
        """Process all the children of the "TestSteps" element in the test case.
        
        Args:
            test_case (:class:`TestCase`) = Add "TestPrep" objects to this test case.
            xml_test_steps ([etree]) = A list of etree elements that children of "TestSteps".
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The TestPrep was invalid in some way.
        """
        
        for xml_test_step in xml_test_steps:
            if xml_test_step.tag == 'Step':
                self._process_step(test_case, xml_test_step)
            else:
                self._process_resource_refresh(test_case, xml_test_step)
            
    def _process_test_cases(self, xml_test_cases):
        """Process all the "TestCase" elements defined in the 'VirtualMachineHost' etree element.
        
        Args:
            xml_test_cases (etree) = An etree element representing a "TestCase".
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: Duplicate TestCase names exist in TestPlanConfig.
        """
        
        for xml_test_case in xml_test_cases:
            test_case_name = xml_test_case.attrib['name']
            
            if test_case_name in self._content.get_test_cases.keys():
                raise ConfigError('Duplicate test case name "{0}" was discovered in the "{1}" '
                                  'test plan!'.format(test_case_name, 
                                                      self._config_file), 
                                  self._config_file)
                
            test_case = TestCase(test_case_name)
            
            self._process_test_preps(test_case, xml_test_case.findall('.//PrepareVirtualMachine'))
            
            self._process_test_steps(test_case, list(xml_test_case.find('.//TestSteps')))
            
            self._content.add_test_case(test_case_name, test_case)
            
    def _load_xsd(self):
        """Load the XSD document and verify that it is proper.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The XSD has incorrect format.
        """
        
        super(TestPlanConfig, self)._load_xsd()
        
    def validate_config(self, suppress_exceptions=False):
        """This method will use the XSD document to validate the content of the associated config
        file.
        
        Args:
            suppress_exceptions (bool): Only return True/False and stop all exceptions from popping.
        
        Returns:
            (bool)
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated XML Schema.
        """
        
        super(TestPlanConfig, self).validate_config(suppress_exceptions)

    def parse_config(self, validate=True):
        """This method will use the XSD document to validate the content of the associated config
        file.
        
        Args:
            validate (bool): Enable config validation against XSD.
        
        Returns:
            (bool)
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated
                XML Schema or config does not have valid XML formatting.
        """
        
        super(TestPlanConfig, self).parse_config(validate)
        
    def __getitem__(self, key):
        """This method extends the container lookup of the class objects so you can access content
        items directly without resorting to the using the '_content' dictionary.
        
        Returns:
           (obj)
           
        Raises:
            KeyError: The specified key does not exist.
        """
        
        return self._content.get_test_cases[key]
    
    def __iter__(self):
        """Provide an iterator for the internal '_content' dictionary.
        
        Returns:
           (iterator)
           
        Raises:
            None
        """
        
        return self._content.get_test_cases.__iter__()
    
    @property
    def get_test_plan(self):
        """Return the "TestPlan object for this config.
        
        Returns:
            |:class:`TestPlan`|
        """
        
        return self._content


class TestRunConfig(_Config):
    """This class will validate, parse and store information contained in the TestRunConfig.
    
    Args:
        xml_config_path (str) = The path to the XML config file that contains information to be 
            parsed and stored.
        xsd_file (str) = The path to the XSD file to use for XML validation.
        
    Raises:
        :class:`ConfigError`: The XML config file does not conform the associated XML Schema or 
            config does not have valid XML formatting.
    """
    
    def __init__(self, xml_config_path, xsd_path):
        super(TestRunConfig, self).__init__(xml_config_path, xsd_path)

        # Instantiate logging object.
        self.logger = logging.getLogger('bespoke.config.TestRunConfig')

        self.parse_config()
        self.load_content()
        
    def load_content(self):
        """Load all the content from the config document into the object.
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated
                XML Schema or config does not have valid XML formatting.
        """
        
        # Get the root of the config.
        xml_root = self._xml_config_doc.getroot()
        
        # Populate the content dictionary.
        self._extract_simple_text(self._content, xml_root, 'Description')
        self._extract_simple_text(self._content, xml_root, 'EmailSender', self.valid_email)
        self._extract_simple_text(self._content, xml_root, 'EmailSubject')
        self._extract_simple_text(self._content, xml_root, 'SMTPServer', self.valid_network_address)
        self._extract_simple_attrib(self._content, xml_root, 'SMTPServer', 'port', self.valid_port)
        self._extract_simple_text(self._content, xml_root.find('SMTPCredentials'), 'Username')
        self._extract_simple_text(self._content, xml_root.find('SMTPCredentials'), 'Password')
        self._extract_simple_attrib(self._content, xml_root, 'SMTPCredentials', 'security_type')
        self._extract_simple_attrib(self._content, xml_root, 'SMTPCredentials', 'self_signed')
        
        self._extract_list_simple_text(self._content, 
                                       xml_root.find('EmailRecipients'), 
                                       'EmailRecipient', 
                                       'EmailRecipients',
                                       self.valid_email)
        self._extract_list_simple_text(self._content, 
                                       xml_root.find('ToolConfigs'), 
                                       'ToolConfig', 
                                       'ToolConfigs',
                                       self.valid_path)
        self._extract_list_simple_text(self._content, 
                                       xml_root.find('BuildConfigs'), 
                                       'BuildConfig', 
                                       'BuildConfigs',
                                       self.valid_path)
        self._extract_list_simple_text(self._content, 
                                       xml_root.find('TestPlans'), 
                                       'TestPlan', 
                                       'TestPlans',
                                       self.valid_path)
        
        self._convert_content_data(self._content)
    
    def _convert_content_data(self, content):
        """Convert that data type of some of the content to a more appropriate type.
        
        Args:
            content ({str:obj}) = A dictionary holding configuration information.
        
        Returns:
            None.
        
        Raises:
            None.
        """
        
        content['port'] = int(content['port'])
        content['self_signed'] = False if content['self_signed'] in ('0', 'false') else True
        
    def _load_xsd(self):
        """Load the XSD document and verify that it is proper
        
        Args:
            None.
        
        Returns:
            None.
        
        Raises:
            :class:`ConfigError`: The XSD has incorrect format.
        """
        
        super(TestRunConfig, self)._load_xsd()
        
    def validate_config(self, suppress_exceptions=False):
        """This method will use the XSD document to validate the content of the associated config
        file.
        
        Args:
            suppress_exceptions (bool): Only return True/False and stop all exceptions from popping.
        
        Returns:
            (bool)
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated XML Schema.
        """
        
        super(TestRunConfig, self).validate_config(suppress_exceptions)
    
    def parse_config(self, validate=True):
        """This method will use the XSD document to validate the content of the associated config
        file.
        
        Args:
            validate (bool): Enable config validation against XSD.
        
        Returns:
            (bool)
        
        Raises:
            :class:`ConfigError`: The XML config file does not conform the associated
                XML Schema or config does not have valid XML formatting.
        """
        
        super(TestRunConfig, self).parse_config(validate)
    
    def __getitem__(self, key):
        """This method extends the container lookup of the class objects so you can access content
        items directly without resorting to the using the '_content' dictionary.
        
        Returns:
           (obj)
           
        Raises:
            KeyError: The specified key does not exist.
        """
        
        return super(TestRunConfig, self).__getitem__(key)
    
    def __iter__(self):
        """Provide an iterator for the internal '_content' dictionary.
        
        Returns:
           (iterator)
           
        Raises:
            None
        """
        
        return super(TestRunConfig, self).__iter__()


# ===================================================================================================
#  Exceptions
# ===================================================================================================
class ConfigError(Exception):
    """This is a base exception for the config module.
    
    Args:
        msg (str): The error message.
        _config_file (str): The path to the config file with the error.
    """
    
    def __init__(self, msg, config_file=''):
        self.message = self.msg = msg
        self._config_file = config_file
    
    def __str__(self):
        return "ConfigError: {0} Config File: {1}".format(self.msg, self._config_file)