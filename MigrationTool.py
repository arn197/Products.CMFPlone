from Globals import InitializeClass, DTMLFile, DevelopmentMode
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem

from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.CMFCorePermissions import ManagePortal

import zLOG
import traceback
import sys
import types

def log(message,summary='',severity=0):
    zLOG.LOG('Plone: ',severity, summary, message)

_upgradePaths = {}
_widgetRegistry = {}

class MigrationTool( UniqueObject, SimpleItem):
    id = 'portal_migration'
    meta_type = 'Plone Migration Tool'

    _needRecatalog = 0
    _needUpdateRole = 0

    manage_options = ( 
        { 'label' : 'Overview', 'action' : 'manage_overview' }, 
        { 'label' : 'Migrate', 'action' : 'manage_migrate' }, 
        { 'label' : 'Setup', 'action' : 'manage_setup' }, 
        )

    security = ClassSecurityInfo()

    security.declareProtected(ManagePortal, 'manage_overview')
    security.declareProtected(ManagePortal, 'manage_results')
    security.declareProtected(ManagePortal, 'manage_migrate')
    security.declareProtected(ManagePortal, 'manage_setup')
    
    manage_migrate = DTMLFile('www/migrationRun', globals())
    manage_overview = DTMLFile('www/migrationTool', globals())
    manage_results = DTMLFile('www/migrationResults', globals())
    manage_setup = DTMLFile('www/migrationSetup', globals())

    # Add a visual note
    def om_icons(self):
        icons = ({
                    'path':'misc_/CMFPlone/tool.gif',
                    'alt':self.meta_type,
                    'title':self.meta_type,
                 },)
        if self.needUpgrading() \
           or self.needUpdateRole() \
           or self.needRecatalog():
           icons = icons + ({
                    'path':'misc_/PageTemplates/exclamation.gif',
                    'alt':'Error',
                    'title':'This Plone instance needs updating'
                 },)
        
        return icons

    ##############################################################
    # Public methods
    #
    # versions methods

    security.declareProtected(ManagePortal, 'getInstanceVersion')
    def getInstanceVersion(self):
        """ The version this instance of plone is on """
        if getattr(self, '_version', None) is None:
            self.setInstanceVersion(self.getFileSystemVersion())
        return self._version.lower()

    security.declareProtected(ManagePortal, 'setInstanceVersion')
    def setInstanceVersion(self, version):
        """ The version this instance of plone is on """
        self._version = version

    security.declareProtected(ManagePortal, 'knownVersions')
    def knownVersions(self):
        """ All known version ids, except current one """
        return _upgradePaths.keys()

    security.declareProtected(ManagePortal, 'getFileSystemVersion')
    def getFileSystemVersion(self):
        """ The version this instance of plone is on """
        return self.Control_Panel.Products.CMFPlone.version.lower()

    security.declareProtected(ManagePortal, 'needUpgrading')
    def needUpgrading(self):
        """ Need upgrading? """
        return self.getInstanceVersion() != self.getFileSystemVersion()
        

    security.declareProtected(ManagePortal, 'coreVersions')
    def coreVersions(self):
        """ Useful core information """
        vars = {}
        cp = self.Control_Panel
        vars['Zope'] = cp.version_txt
        vars['Python'] = cp.sys_version
        vars['Platform'] = cp.sys_platform
        vars['Plone Instance'] = self.getInstanceVersion()
        vars['Plone File System'] = self.getFileSystemVersion()
        vars['CMF'] = cp.Products.CMFCore.version
        vars['Debug mode'] = DevelopmentMode and 'Yes' or 'No'
        return vars

    security.declareProtected(ManagePortal, 'coreVersionsList')
    def coreVersionsList(self):
        """ Useful core information """
        res = self.coreVersions().items()
        res.sort()
        return res
   
    security.declareProtected(ManagePortal, 'needUpdateRole')
    def needUpdateRole(self):
        """ Do roles need to be updated? """
        return self._needUpdateRole
    
    security.declareProtected(ManagePortal, 'needRecatalog')
    def needRecatalog(self):
        """ Does this thing now need recataloging? """
        return self._needRecatalog
        
    ##############################################################
    # the setup widget registry
    # this is a whole bunch of wrappers
    # Really an unprotected sub object 
    # declaration could do this...
    
    def _getWidget(self, widget):
        """ We cant instantiate widgets at run time
        but can send all get calls through here... """
        _widget = _widgetRegistry[widget]
        if isinstance(_widget, types.ClassType):
            w = _widget(self.aq_parent, self)
            _widgetRegistry[widget] = w
            return w
            
        return _widget
                
    security.declareProtected(ManagePortal, 'listWidgets')
    def listWidgets(self):
        """ List all the widgets """
        return _widgetRegistry.keys()

    security.declareProtected(ManagePortal, 'getDescription')
    def getDescription(self, widget):
        """ List all the widgets """
        return self._getWidget(widget).description
    
    security.declareProtected(ManagePortal, 'listAvailable')
    def listAvailable(self, widget):
        """  List all the Available things """
        return self._getWidget(widget).available()

    security.declareProtected(ManagePortal, 'listInstalled')
    def listInstalled(self, widget):
        """  List all the installed things """
        return self._getWidget(widget).installed()
    
    security.declareProtected(ManagePortal, 'listNotInstalled')
    def listNotInstalled(self, widget):
        """ List all the not installed things """
        avail = self.listAvailable(widget)
        install = self.listInstalled(widget)
        return [ item for item in avail if item not in install ]
   
    security.declareProtected(ManagePortal, 'activeWidget')        
    def activeWidget(self, widget):
        """ Show the state """
        return self._getWidget(widget).active()

    security.declareProtected(ManagePortal, 'setupWidget')        
    def setupWidget(self, widget):
        """ Show the state """
        return self._getWidget(widget).setup()
                            
    security.declareProtected(ManagePortal, 'alterItems')        
    def alterItems(self, widget=None, items=[]):
        """ Figure out which items to install and which to uninstall """
        installed = self.listInstalled(widget)
        
        toAdd = [ item for item in items if item not in installed ] 
        toDel = [ install for install in installed if install not in items ]

        out = []
        if toAdd: out += self.installItems(widget, toAdd)
        if toDel: out += self.uninstallItems(widget, toDel)
        return self.manage_results(self, out=out)
        
    security.declareProtected(ManagePortal, 'installItems')
    def installItems(self, widget, items):
        """ Install the items """
        return self._getWidget(widget).addItems(items)
                
    security.declareProtected(ManagePortal, 'uninstallItems')
    def uninstallItems(self, widget, items):
        """ Uninstall the items """
        return self._getWidget(widget).delItems(items)
        
    ##############################################################

    security.declareProtected(ManagePortal, 'upgrade')
    def upgrade(self, REQUEST=None, dry_run=None):
        """ perform the upgrade """
        # keep it simple
        out = []

        self._check()

        if dry_run:
            out.append(("Dry run selected.", zLOG.INFO))
            
        # either get the forced upgrade instance or the current instance
        newv = getattr(REQUEST, "force_instance_version", self.getInstanceVersion())
       
        out.append(("Starting the migration from version: %s" % newv, zLOG.INFO))
        while newv is not None:
            out.append(("Attempting to upgrade from: %s" % newv, zLOG.INFO))
            try:
                newv = self._upgrade(newv)
                if newv is not None:
                    out.append(("Upgrade to: %s, completed" % newv, zLOG.INFO))
                    self.setInstanceVersion(newv)
                else:
                    out.append(("No upgrade path found from that version, migration stopping", zLOG.INFO))
            except:
                out.append(("Upgrade aborted", zLOG.ERROR))
                for line in traceback.format_tb(sys.exc_traceback):
                    out.append((line, zLOG.ERROR))
                    
                err_log=self.error_log
                err_log.raising(sys.exc_info())
                
                # set newv to None
                # to break the loop
                newv = None
                
        out.append(("End of upgrade path, migration has finished", zLOG.INFO))
        
        if self.needUpgrading():
            out.append(("The upgrade path did NOT reach current version", zLOG.PROBLEM))
            out.append(("Migration has failed", zLOG.PROBLEM))

        # do this once all the changes have been done
        if self.needRecatalog():
            try:
                self.portal_catalog.refreshCatalog()
                self._needRecatalog = 0
            except:
                out.append(("Exception was thrown while cataloging", zLOG.ERROR))
                out += traceback.format_tb(sys.exc_traceback)

        if self.needUpdateRole():
            try:
                self.portal_workflow.updateRoleMappings()
                self._needUpdateRole = 0
            except:
                out.append(("Exception was thrown while updating role mappings", zLOG.ERROR))
                out += traceback.format_tb(sys.exc_traceback)
                
        if dry_run:
            out.append(("Dry run selected, transaction aborted", zLOG.INFO))
            get_transaction().abort()
    
        # log all this to the ZLOG
        for msg, sev in out:
            log(msg, severity=sev)
        
        return self.manage_results(self, out=out)
        
    ##############################################################
    # Private methods
            
    def _check(self):
        """ Are we inside a Plone site?  Are we allowed? """
        if not hasattr(self,'portal_url'):
            raise 'You must be in a Plone site to migrate.'      

    def _upgrade(self, version):
        version = version.lower()
        if not _upgradePaths.has_key(version): 
            return None

        newversion, function = _upgradePaths[version]
        function(self.aq_parent)
        return newversion
    
def registerUpgradePath(oldversion, newversion, function): 
    """ Basic register func """
    _upgradePaths[oldversion.lower()] = [newversion.lower(), function]
   
def registerSetupWidget(widget):
    """ Basic register things """
    _widgetRegistry[widget.type] = widget

InitializeClass(MigrationTool)
