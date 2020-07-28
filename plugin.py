# OS
import os
from datetime import datetime
from time import time, strftime
from Components.About import about
from boxbranding import getBoxType, getMachineBuild
from enigma import eTimer, iPlayableService, iServiceInformation
from Components.ServiceEventTracker import ServiceEventTracker

# GUI screens
from Screens.Screen import Screen
from Screens.TextBox import TextBox
from Screens.MessageBox import MessageBox
from Components.ConfigList import ConfigListScreen

# Data structures
from enigma import ePoint
from collections import deque
from Components.Label import Label
from Components.Sources.Boolean import Boolean
from Components.Sources.StaticText import StaticText
from Components.config import config, ConfigSubsection, getConfigListEntry
from Components.config import ConfigSelection, ConfigSelectionNumber, ConfigYesNo
from Components.ActionMap import ActionMap

# Misc
from Components.config import KEY_LEFT, KEY_RIGHT, KEY_HOME, KEY_END
from Plugins.Plugin import PluginDescriptor


class GUI(Screen, ConfigListScreen):
	
	instance = None
	isOpen = False

	def __init__(self, session):			
		
		GUI.instance = self	
		log("GUI.__init__() start")	
		
		Screen.__init__(self, session)
		self.session = session
		self.skinName = ["Setup"]
		self.setup_title = _("AutoSharpness v1.0")	
		self["footnote"] = Label()
		self["description"] = Label()			
		self.list = []
		
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
		self.createConfig("GUI.__init__() ")
		
		self["actions"] = ActionMap(["SetupActions", "ColorActions", "MenuActions"],
		{		
			"red": self.keyRed, "cancel": self.keyRed,		
			"green": self.keyGreen,
			"yellow": self.keyYellow,
			"blue": self.keyBlue,		
			#"info": self.keyInfo,
			#"menu": self.keyMenu,			
		}, -2)		
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Load defaults"))
		self["key_yellow"] = StaticText(_("View log"))
		self["key_blue"] = StaticText(_("About"))
		
		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)
			
		#self.changedEntry(caller="GUI.__init__() ")
		self.onLayoutFinish.append(self.layoutFinished)
		
		log("GUI.__init__() config: " + Daemon.instance.getConfigString())	
		log("GUI.__init__() finish")
	
	def keyRed(self):
		GUI.isOpen = False
		log("GUI.keyRed()")
		self.keySave() # saves all keys in self["config"].list to file and calls self.close()	
		
	def keyGreen(self):
		log("GUI.keyGreen()")
		self.session.openWithCallback(self.keyGreenConfirm, GUI_MyMessageBox, _("Load defaults for all settings?"), MessageBox.TYPE_YESNO, timeout = 20, default = False)
			
	def keyGreenConfirm(self, confirmed):
		
		if confirmed:
		
			if Daemon.instance.sharpnessSupported: config.plugins.autosharpness.enabled.value = True
			else: config.plugins.autosharpness.enabled.value = False	
			
			config.plugins.autosharpness.increment.value = "32"	
			config.plugins.autosharpness.sharpness_480i576i.value = 0
			config.plugins.autosharpness.sharpness_480p576p.value = 0
			config.plugins.autosharpness.sharpness_720p.value = 0
			config.plugins.autosharpness.sharpness_1080i.value = 0
			config.plugins.autosharpness.sharpness_1080p.value = 0
			config.plugins.autosharpness.sharpness_2160p.value = 0
			config.plugins.autosharpness.delay.value = "1.5 seconds"
			config.plugins.autosharpness.label.value = "5 seconds"
			
			if Daemon.instance.pepSupported: config.plugins.autosharpness.applyby.value = "Config"
			else: config.plugins.autosharpness.applyby.value = "Proc"		
			
			config.plugins.autosharpness.applydiscreetly.value = "No"		
			
			config.plugins.autosharpness.enforce.value = "No"
			Daemon.instance.enforceTimer.stop()
			Daemon.instance.enforceTimer.start(Daemon.instance.getEnforceFrequency("Timer"), True)			
			
			config.plugins.autosharpness.detectionlevel.value = "Normal"
			
			if Daemon.instance.hasHisiChipset and Daemon.instance.boxType == "beyonwizv2":
				config.plugins.autosharpness.applyhisifix.value = "Yes"
				config.plugins.autosharpness.detectionlevel.value = "High"
			else: config.plugins.autosharpness.applyhisifix.value = "No"
			
			if (config.plugins.autosharpness.enabled.value):
				Daemon.instance.previousStreamRes = "Unknown"
				Daemon.instance.setSharpness("GUI.keyGreenConfirm() ")
				if (config.plugins.autosharpness.applyhisifix.value == "Yes"):
					Daemon.instance.setHisiFix("GUI.keyGreenConfirm() ")
			
			self.createConfig("GUI.keyGreenConfirm() ")
			self.saveAll() # saves all keys in self["config"].list to file
						
	def keyYellow(self):
		log("GUI.keyYellow()")
		self.session.open(GUI_ViewLog, "\n".join(Daemon.log))
		
	def keyBlue(self):
		log("GUI.keyBlue()")	
		msgBox = self.session.open(MessageBox,_("AutoSharpness v1.0 by S.Z.\nTiny.cc/AutoSharpness"), MessageBox.TYPE_INFO)
		msgBox.setTitle(_("About"))	
		
	def selectionChanged(self, caller=""):	# also called on GUI creation
				
		#log("%sGUI.selectionChanged()" % caller)	
		self["description"].setText(self["config"].getCurrent()[2])
		
		if "*" in self["config"].getCurrent()[0]:
			self["footnote"].setText("  * Active setting")
		else:
			self["footnote"].setText("")
				
	def keyLeft(self): # occurs before changedEntry	
		#log("GUI.keyLeft()")
		if "*" in self["config"].getCurrent()[0]:
			self.session.openWithCallback(self.sharpnessSetterClosed,
				GUI_SharpnessSetter, configEntry = self["config"].getCurrent())		
		else:
			ConfigListScreen.keyLeft(self)
			
	def keyRight(self): # occurs before changedEntry
		#log("GUI.keyRight()")
		if "*" in self["config"].getCurrent()[0]:
			self.session.openWithCallback(self.sharpnessSetterClosed,
				GUI_SharpnessSetter, configEntry = self["config"].getCurrent())	
		else:
			ConfigListScreen.keyRight(self)
		
	def changedEntry(self, caller=""):
	
		entry = self["config"].getCurrent()[1]
			
		if (entry == config.plugins.autosharpness.enforce):
			Daemon.instance.enforceTimer.stop()
			Daemon.instance.enforceTimer.start(Daemon.instance.getEnforceFrequency("Timer"), True)
		
		if (entry == config.plugins.autosharpness.detectionlevel):
			if (config.plugins.autosharpness.applyhisifix.value == "Yes"):
				config.plugins.autosharpness.detectionlevel.value = "High"
				
		if (entry == config.plugins.autosharpness.applyhisifix):
			if (config.plugins.autosharpness.applyhisifix.value == "Yes"):
				config.plugins.autosharpness.detectionlevel.value = "High"
				Daemon.instance.setHisiFix("%sGUI.changedEntry() " % caller)	
				
		if (entry == config.plugins.autosharpness.enabled):
	
			if (config.plugins.autosharpness.enabled.value):
				
				if (Daemon.instance.sharpnessSupported == False):				
					config.plugins.autosharpness.enabled.value = False				
					msgBox = self.session.open(MessageBox,_("Your box does not appear to support picture sharpness control: path 'proc/stb/vmpeg/0/pep_sharpness' was not found."), MessageBox.TYPE_ERROR)
					msgBox.setTitle(_("Error"))
				else:
					Daemon.instance.previousStreamRes = "Unknown"
					Daemon.instance.setSharpness("%sGUI.changedEntry() " % caller)
					if (config.plugins.autosharpness.applyhisifix.value == "Yes"):
						Daemon.instance.setHisiFix("%sGUI.changedEntry() " % caller)
				
		self.createConfig("%sGUI.changedEntry() " % caller)
	
	def sharpnessSetterClosed(self):		
		self["config"].invalidate(self["config"].getCurrent())
		self.createConfig("GUI.sharpnessSetterClosed() ")
		log("GUI.sharpnessSetterClosed() config: " + Daemon.instance.getConfigString())
			
	def layoutFinished(self, caller=""):
		log("GUI.layoutFinished()")
		self.setTitle(self.setup_title)
		Daemon.instance.notificationLabel.hide()	
		GUI.isOpen = True
		
	def createConfig(self, caller=""):	# calls selectionChanged() if cursor happens to be on a GUI element
										# which changes as a result of this func
		
		log("%sGUI.createConfig()" % caller)
		
		self.configlist = []

		if (Daemon.instance.boxType != "Unknown") and (Daemon.instance.chipset != "Unknown"):
			appendString = " (" + Daemon.instance.boxType.capitalize() + "; " + Daemon.instance.chipset + ")."
		else: appendString = "."		
		
		self.configlist.append(getConfigListEntry(_("Enable AutoSharpness"), config.plugins.autosharpness.enabled,
		_("Enables this plugin, which allows you to set different picture sharpness values according to the resolution of the video content.  Please note the quality of the picture sharpening is dependent on the algorithm used by the chipset driver of your box" + appendString)))	
				
		if (config.plugins.autosharpness.enabled.value):

			self.configlist.append(getConfigListEntry(_("Sharpness step size"), config.plugins.autosharpness.increment,
			_("Sets the sharpness adjustment step size.  The default is 32, which provides 8 steps of adjustment between the range of 0 and 256.")))
					
			descriptions = ["Sharpness for 480i / 576i", "Sharpness for 480p / 576p", "Sharpness for 720p",
							"Sharpness for 1080i", "Sharpness for 1080p", "Sharpness for 2160p"]
			for i, e in enumerate(descriptions):
				descriptions[i] = e + " *" if Daemon.instance.previousStreamRes in e else e
					
			self.configlist.append(getConfigListEntry(_(descriptions[0]), config.plugins.autosharpness.sharpness_480i576i,_("Sets the sharpness value to apply when the video content is 480i or 576i.")))
			self.configlist.append(getConfigListEntry(_(descriptions[1]), config.plugins.autosharpness.sharpness_480p576p,
			_("Sets the sharpness value to apply when the video content is 480p or 576p.")))		
			self.configlist.append(getConfigListEntry(_(descriptions[2]), config.plugins.autosharpness.sharpness_720p,
			_("Sets the sharpness value to apply when the video content is 720p.")))		
			self.configlist.append(getConfigListEntry(_(descriptions[3]), config.plugins.autosharpness.sharpness_1080i,
			_("Sets the sharpness value to apply when the video content is 1080i.")))	
			self.configlist.append(getConfigListEntry(_(descriptions[4]), config.plugins.autosharpness.sharpness_1080p,
			_("Sets the sharpness value to apply when the video content is 1080p.")))
			self.configlist.append(getConfigListEntry(_(descriptions[5]), config.plugins.autosharpness.sharpness_2160p,
			_("Sets the sharpness value to apply when the video content is 2160p.")))
					
		
			self.configlist.append(getConfigListEntry(_("Delay"), config.plugins.autosharpness.delay,
			_("Sets the time delay before applying a sharpness setting when the video content changes.  The default is 1.5 seconds.")))
			
			self.configlist.append(getConfigListEntry(_("Show notification label"), config.plugins.autosharpness.label,
			_("Controls the display and duration of a notification label which pops up whenever a sharpness setting is automatically applied.  The default is 5 seconds.  Note: if you have enabled the infobar fade-out effect in system settings, it may interfere with the display of the notification label.")))
			
			
			if Daemon.instance.pepSupported:
				self.configlist.append(getConfigListEntry(_("Application method"), config.plugins.autosharpness.applyby,
				_("Controls which system setting will be used to apply sharpness values.  Config uses config.pep.sharpness; Proc uses proc/stb/vmpeg/0/pep_sharpness.  The default is Config.")))
									
			self.configlist.append(getConfigListEntry(_("Apply discreetly"), config.plugins.autosharpness.applydiscreetly,
			_("Controls whether to only apply a sharpness setting if the resolution of the video content changes.  Otherwise it will be applied at the beginning of every new video stream.  The default is No.")))
			
			self.configlist.append(getConfigListEntry(_("Enforce sharpness"), config.plugins.autosharpness.enforce,
			_("Controls how often to enforce the active sharpness setting by continuously re-applying it.  The default is No, which disables this behaviour.  If enabled, the apply discreetly setting will be ignored.")))
			
			self.configlist.append(getConfigListEntry(_("Video detection level"), config.plugins.autosharpness.detectionlevel,
			_("If set to high, more system events will be monitored when trying to detect changes to the resolution of the video content.  If certain media files are not being detected, try setting this value to high, otherwise the default value is normal.")))
			
			if Daemon.instance.hasHisiChipset:
				self.configlist.append(getConfigListEntry(_("Enable 3798mv200 fix"), config.plugins.autosharpness.applyhisifix,
				_("If enabled, AutoSharpness will try to prevent a driver bug which interferes with the sharpness setting on boxes with chipset 3798mv200.  As a side effect you may notice the picture size change slightly when zapping between video streams.  If enabled, video detection level will be forced to high.")))

			
		self["config"].list = self.configlist
		self["config"].l.setList(self.configlist)
		if config.usage.sort_settings.value: self["config"].list.sort()
		

class GUI_SharpnessSetter(Screen, ConfigListScreen):

	instance = None
	isOpen = False
	
	skin = """
		<screen name="GUI_SharpnessSetter" position="center,e-130" size="560,100" backgroundColor="un44000000" flags="wfNoBorder" title="AutoSharpness" >	
		<widget position="10,10" size="555,75" name="config" scrollbarMode="showOnDemand"/>	
		<widget position="center,66" size="200,25" source="key_red" render="Label" foregroundColor="red" font="Regular;20" halign="center" valign="center" backgroundColor="black" transparent="1" zPosition="3"/>
		</screen>"""
			
	def __init__(self, session, configEntry = None):
		
		GUI_SharpnessSetter.instance = self	
		log("GUI_SharpnessSetter.__init__() start")	
		
		Screen.__init__(self, session)
		self.session = session
		self.configEntry = configEntry
		self.setup_title = _("AutoSharpnessPreview")
		
		self.list = []	
		ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
		self.createConfig("GUI_SharpnessSetter.__init__() ")
		
		self["actions"] = ActionMap(["SetupActions", "ColorActions", "MenuActions"],
		{
			"red": self.keyRed, "cancel": self.keyRed,
		}, -2)
		self["key_red"] = StaticText(_("Close"))

		if not self.selectionChanged in self["config"].onSelectionChanged:
			self["config"].onSelectionChanged.append(self.selectionChanged)		

		self.onLayoutFinish.append(self.layoutFinished)

		log("GUI_SharpnessSetter.__init__() config: " + Daemon.instance.getConfigString())
		log("GUI_SharpnessSetter.__init__() finish")
		
	def keyRed(self, caller=""):
		GUI_SharpnessSetter.isOpen = False
		log("%sGUI_SharpnessSetter.keyRed()" % caller)
		self.close()
		
	def layoutFinished(self):
		log("GUI_SharpnessSetter.layoutFinished()")
		self.setTitle(self.setup_title)
		GUI_SharpnessSetter.isOpen = True
	
	def selectionChanged(self, caller=""): # also called on GUI creation	
		#log("%sGUI_SharpnessSetter.selectionChanged()" % caller)
		pass
	
	def changedEntry(self, caller=""):				
		if (self["config"].getCurrent()[1] == self.configEntry[1]):
			self.setSharpness(int(self.configEntry[1].value), "%sGUI_SharpnessSetter.changedEntry() " % caller)
		else:
			log("%sGUI_SharpnessSetter.changedEntry()" % caller)
		
	def createConfig(self, caller=""):
		log("%sGUI_SharpnessSetter.createConfig()" % caller)	
		self.configlist = []
	
		#self.configlist.append(self.configEntry)
		self.configlist.append(getConfigListEntry( _(str(self.configEntry[0]).replace(" *", "")),
								self.configEntry[1], self.configEntry[2]))
	
		self.configlist.append(getConfigListEntry(_("Sharpness step size"), config.plugins.autosharpness.increment,
		_("Sets the sharpness adjustment step size.  The default is 32, which provides 8 steps of adjustment between the range of 0 and 256.")))
		self["config"].list = self.configlist
		self["config"].l.setSeperation(300)
		self["config"].l.setList(self.configlist)
	
	def setSharpness(self, newSharpness, caller=""):	
		
		applyBy = str(config.plugins.autosharpness.applyby.value)
		
		if (applyBy == "Config") or (applyBy == "Config+proc"):
			try: 
				config.pep.sharpness.value = newSharpness
				config.pep.sharpness.save()
				log("%sGUI_SharpnessSetter.setSharpness() wrote %s to config.pep.sharpness, which now contains: %s" \
					% (caller, newSharpness, str(config.pep.sharpness.value)))
			except:
				log("%sGUI_SharpnessSetter.setSharpness() failed writing %s to config.pep.sharpness" \
					% (caller, newSharpness))
						
		if (applyBy == "Proc") or (applyBy == "Config+proc"):

			if os.path.exists("/proc/stb/vmpeg/0/pep_sharpness"):
				try:
					val = int(newSharpness * 256)
					f = open("/proc/stb/vmpeg/0/pep_sharpness", "w")
					f.write("%0.8X" % val)
					f.close()
					log("%sGUI_SharpnessSetter.setSharpness() wrote %0.8X to proc/stb/vmpeg/0/pep_sharpness" \
						% (caller, val))
				except IOError:
					log("%sGUI_SharpnessSetter.setSharpness() failed writing to proc/stb/vmpeg/0/pep_sharpness; " \
						"returning" % caller) 
					return
			else:
				log("%sGUI_SharpnessSetter.setSharpness() path not found: proc/stb/vmpeg/0/pep_sharpness; " \
					"returning" % caller) 
				return
								
			if os.path.exists("/proc/stb/vmpeg/0/pep_apply"):	
				try:
					# time.sleep(0.1) ?
					f = open("/proc/stb/vmpeg/0/pep_apply", "w")
					f.write("1")
					f.close()
					log("%sGUI_SharpnessSetter.setSharpness() wrote 1 to proc/stb/vmpeg/0/pep_apply" % caller)
				except IOError:
					log("%sGUI_SharpnessSetter.setSharpness() failed writing to /proc/stb/vmpeg/0/pep_apply; " \
						"continuing anyway" % caller)
			else:
				log("%sGUI_SharpnessSetter.setSharpness() path not found: proc/stb/vmpeg/0/pep_apply; " \
					"continuing anyway" % caller)

					
class GUI_ViewLog(TextBox):	
	skin = """<screen name="GUI_ViewLog" backgroundColor="un44000000" position="50,75" size="1180,595" title="AutoSharpness Log"> <widget font="Regular;14" name="text" position="0,4" size="1180,591"/> </screen>"""

	
class GUI_NotificationLabel(Screen):
	
	def __init__(self, session):
		
		self.skin = """
		<screen name="GUI_NotificationLabel" position="e-260,155" size="210,50" flags="wfNoBorder" backgroundColor="#7f110000" zPosition="11" >
		<widget name="resolution" position="10,5" size="195,20" font="Regular;18" transparent="1" />
		<widget name="sharpness" position="10,25" size="195,20" font="Regular;18" transparent="1" />
		</screen>"""
		
		Screen.__init__(self, session)
		self["resolution"] = Label()
		self["sharpness"] = Label()
		self.notificationTimer = eTimer()
		self.notificationTimer.callback.append(self.hide)
		self.onShow.append(self.hideNotificationLabel)

	def hideNotificationLabel(self):	
		lut = {"No":"No","1 second":1000,"2 seconds":2000,"3 seconds":3000,"5 seconds":5000,
				"8 seconds":8000,"10 seconds":10000,"12 seconds":12000,"15 seconds":15000}
		delay = lut[config.plugins.autosharpness.label.value]
		if (delay != "No"):
			self.notificationTimer.start(delay, True)	

			
class GUI_PictureInGraphics(Screen):

	def __init__(self, session):	
		#log("GUI_PictureInGraphics.__init__() start")	
		zPosition = """ zPosition="-1" """ # -1/1/12/blank
		self.skin = """<screen name="GUI_PictureInGraphics" position="0,0" size="1280,720" backgroundColor="#ff000000" transparent="0" flags="wfNoBorder" %s> <widget position="0,0" size="1280,720" source="session.VideoPicture" render="Pig" zPosition="1" backgroundColor="#ff000000"/></screen>""" % zPosition
		Screen.__init__(self, session)
		
		
class GUI_MyMessageBox(MessageBox):

	def alwaysOK(self):
		pass # avoid green keybounce causing reset to default


class MyConfigSelectionNumber(ConfigSelectionNumber):

	def handleKey(self, key):
		now = time()
		if key == self.keyLast and now - self.keyTime < 0.25:
			self.keyRepeat += 1
		else:
			self.keyRepeat = 0
		self.keyTime = now
		self.keyLast = key
		nchoices = len(self.choices)
		if nchoices > 1:		
			# if (int(config.plugins.autosharpness.increment.value) == 1):
				# step = 1
				# if self.keyRepeat >= 10:
					# log("handleKey() >=10: %s" % self.keyRepeat)
					# if not self.keyRepeat & 1: # step every second repeat
						# return
					# step = 8
					# if self.keyRepeat >= 20:
						# log("handleKey() >=20: %s" % self.keyRepeat)
						# step = 16
			# else: step = int(config.plugins.autosharpness.increment.value)		
			step = int(config.plugins.autosharpness.increment.value)

			i = self.choices.index(str(self.value))
			if not self.wraparound:
				if key == KEY_RIGHT:
					if i == nchoices - 1:
						return
					if i + step >= nchoices - 1:
						key = KEY_END
				if key == KEY_LEFT:
					if i == 0:
						return
					if i - step <= 0:
						key = KEY_HOME
			if key == KEY_LEFT:
				self.value = self.choices[(i + nchoices - step) % nchoices]
			elif key == KEY_RIGHT:
				self.value = self.choices[(i + step) % nchoices]
			elif key == KEY_HOME:
				self.value = self.choices[0]
			elif key == KEY_END:
				self.value = self.choices[nchoices - 1]


class Daemon(Screen):
	
	instance = None
	log = deque(maxlen=360)
	
	def __init__(self, session):
		
		Daemon.instance = self	
		log("Daemon.__init__() start")
		Screen.__init__(self, session)
		
		self.createConfig("Daemon.__init__() ")	
		log("Daemon.__init__() config: " + self.getConfigString())
				
		self.notificationLabel = session.instantiateDialog(GUI_NotificationLabel)	
		self.pictureInGraphics = self.session.instantiateDialog(GUI_PictureInGraphics)		
		self.setSharpnessTimer = eTimer()
		self.setSharpnessTimer.callback.append(self.setSharpness)	
		self.enforceTimer = eTimer()
		self.enforceTimer.callback.append(self.enforceSharpness)
		self.enforceTimer.start(self.getEnforceFrequency("Timer"), True)
		self.hisiFixTimer = eTimer()
		self.hisiFixTimer.callback.append(self.setHisiFix)	
		self.previousStreamRes = "Unknown"
		
		self.__event_tracker = ServiceEventTracker(screen=self, eventmap=
		{
			iPlayableService.evVideoSizeChanged: self.videoStreamChange,
			iPlayableService.evVideoProgressiveChanged: self.videoStreamChange,
			iPlayableService.evVideoFramerateChanged: self.videoStreamChange,			
			iPlayableService.evStart: self.eventStart,
			iPlayableService.evBuffering: self.bufferChange,
			#iPlayableService.evSeekableStatusChanged: self.seekChange
		})
		
		log("Daemon.__init__() finish")
	
	def createConfig(self, caller=""):
	
		log("%sDaemon.createConfig()" % caller)
			
		boxType = getBoxType(); machineBuild = getMachineBuild(); chipset = about.getChipSetString()	
		if not isinstance(boxType, str):
			if isinstance(machineBuild, str): boxType = machineBuild
			else: boxType = "Unknown"
		self.boxType = boxType; self.machineBuild = machineBuild; self.chipset = chipset
		
		self.configlist = []
		
		config.plugins.autosharpness = \
		ConfigSubsection()	

		config.plugins.autosharpness.enabled = ConfigYesNo(default = False)
		self.configlist.append(config.plugins.autosharpness.enabled)
		self.sharpnessSupported = True if os.path.exists("/proc/stb/vmpeg/0/pep_sharpness") else False	
		if not self.sharpnessSupported: config.plugins.autosharpness.enabled.value = False	
		
		config.plugins.autosharpness.increment = \
		ConfigSelection(choices = ["1","16","32","64","128","256"], default = "32")
		self.configlist.append(config.plugins.autosharpness.increment)
			
		config.plugins.autosharpness.sharpness_480i576i = \
		MyConfigSelectionNumber(min=0, max=256, stepwidth=1, default=0, wraparound=False)
		self.configlist.append(config.plugins.autosharpness.sharpness_480i576i)
		
		config.plugins.autosharpness.sharpness_480p576p = \
		MyConfigSelectionNumber(min=0, max=256, stepwidth=1, default=0, wraparound=False)
		self.configlist.append(config.plugins.autosharpness.sharpness_480p576p)
		
		config.plugins.autosharpness.sharpness_720p = \
		MyConfigSelectionNumber(min=0, max=256, stepwidth=1, default=0, wraparound=False)
		self.configlist.append(config.plugins.autosharpness.sharpness_720p)
		
		config.plugins.autosharpness.sharpness_1080i = \
		MyConfigSelectionNumber(min=0, max=256, stepwidth=1, default=0, wraparound=False)
		self.configlist.append(config.plugins.autosharpness.sharpness_1080i)
		
		config.plugins.autosharpness.sharpness_1080p = \
		MyConfigSelectionNumber(min=0, max=256, stepwidth=1, default=0, wraparound=False)
		self.configlist.append(config.plugins.autosharpness.sharpness_1080p)
		
		config.plugins.autosharpness.sharpness_2160p = \
		MyConfigSelectionNumber(min=0, max=256, stepwidth=1, default=0, wraparound=False)
		self.configlist.append(config.plugins.autosharpness.sharpness_2160p)
		
		choices = ["1 second", "1.5 seconds", "3 seconds", "5 seconds", "8 seconds",
					"10 seconds", "12 seconds", "15 seconds"]
		config.plugins.autosharpness.delay = \
		ConfigSelection(choices = choices, default = "1.5 seconds")
		self.configlist.append(config.plugins.autosharpness.delay)
		
		choices = ["No", "1 second", "2 seconds", "3 seconds", "5 seconds", "8 seconds",
					"10 seconds", "12 seconds", "15 seconds"]
		config.plugins.autosharpness.label = \
		ConfigSelection(choices = choices, default = "5 seconds")
		self.configlist.append(config.plugins.autosharpness.label)
			
		config.plugins.autosharpness.applyby = \
		ConfigSelection(choices = ["Config","Proc","Config+proc"], default = "Config")
		self.configlist.append(config.plugins.autosharpness.applyby)
		try: self.pepSupported = True if isinstance(config.pep.sharpness.value, int) else False
		except: self.pepSupported = False	
		if not self.pepSupported: config.plugins.autosharpness.applyby.value = "Proc"
		
	
		config.plugins.autosharpness.applydiscreetly = \
		ConfigSelection(choices = ["Yes","No"], default = "No")
		self.configlist.append(config.plugins.autosharpness.applydiscreetly)
			
		choices = ["No", "5 seconds", "15 seconds", "30 seconds", "1 minute", "2 minutes", "5 minutes"]
		config.plugins.autosharpness.enforce = \
		ConfigSelection(choices = choices, default = "No")
		self.configlist.append(config.plugins.autosharpness.enforce)
		
		config.plugins.autosharpness.detectionlevel = \
		ConfigSelection(choices = ["Normal","High"], default = "Normal")
		self.configlist.append(config.plugins.autosharpness.detectionlevel)
			
		self.hasHisiChipset = True if (self.chipset in ("3798mv200", "hi3798mv200")) else False
		default = "Yes" if (self.hasHisiChipset and self.boxType == "beyonwizv2") else "No"	
		config.plugins.autosharpness.applyhisifix = ConfigSelection(choices = ["Yes","No"], default=default)
		self.configlist.append(config.plugins.autosharpness.applyhisifix)
		if (config.plugins.autosharpness.applyhisifix.value == "Yes") and (not self.hasHisiChipset):
			config.plugins.autosharpness.applyhisifix.value = "No"	
		if (config.plugins.autosharpness.applyhisifix.value == "Yes"):
			config.plugins.autosharpness.detectionlevel.value = "High"
	
	def getConfigString(self, caller=""):
		s = ""
		for x in self.configlist:
			s += str(x.value) + ","
		return s[:-1]
	
	def eventStart(self):			
		if (config.plugins.autosharpness.detectionlevel.value == "High" or
			config.plugins.autosharpness.applyhisifix.value == "Yes"):
			self.videoStreamChange("Daemon.eventStart() ")
				
	def bufferChange(self):
		bufferInfo = self.session.nav.getCurrentService().streamed().getBufferCharge()
		if (bufferInfo[0] > 98):
			self.videoStreamChange("Daemon.bufferChange() ")
	
	def getEnforceFrequency(self, returnVal):	
			
		lut = {"No":5000,"5 seconds":5000,"15 seconds":15000,"30 seconds":30000,
				"1 minute":60000,"2 minutes":120000,"5 minutes":300000}			
		if (returnVal == "Timer"):
			return lut[config.plugins.autosharpness.enforce.value]			
		elif (returnVal == "Config"):
			return config.plugins.autosharpness.enforce.value

	def getDelay(self):
		
		lut = {"1 second":1000,"1.5 seconds":1500,"3 seconds":3000,"5 seconds":5000,
				"8 seconds":8000,"10 seconds":10000,"12 seconds":12000,"15 seconds":15000}		
		return lut[config.plugins.autosharpness.delay.value]
		
	def enforceSharpness(self):
		
		self.enforceTimer.stop()
		self.enforceTimer.start(self.getEnforceFrequency("Timer"), True)
		
		if (config.plugins.autosharpness.enabled.value == True and
			self.getEnforceFrequency("Config") != "No"):
			self.setSharpness("Daemon.enforceSharpness() ")	
			
	def videoStreamChange(self, caller=""):		
		log("Daemon.videoStreamChange()")
	
		delay = self.getDelay()
		if	(self.session.nav.getCurrentlyPlayingServiceReference() and
			self.session.nav.getCurrentlyPlayingServiceReference().toString().startswith("4097:")):
			delay += 2000
		if (caller == "Daemon.eventStart() "):
			delay += 1500

		self.setSharpnessTimer.stop()
		self.setSharpnessTimer.start(delay, True)
			
		if (config.plugins.autosharpness.applyhisifix.value == "Yes" and
			config.plugins.autosharpness.enabled.value == True):
			self.hisiFixTimer.stop()
			self.hisiFixTimer.start(delay+250, True)
			
	def setHisiFix(self, caller=""):
		log("%sDaemon.setHisiFix()" % caller)
		self.hisiFixTimer.stop()
		try:
			f = open("/proc/stb/video/videomode")
			currentMode = str(f.read()).strip()
			f.close()
		except: currentMode = ""		
		lut = {"2160":2,"1080":2,"720":2,"576":4,"PAL":4,"480":5,"NTSC":5}
		for i in lut: 
			if i in currentMode: nudge = lut[i]; break
			else: nudge = 4
		self.pictureInGraphics.instance.move(ePoint(nudge,nudge))
		self.pictureInGraphics.show()
		self.pictureInGraphics.hide()
		
	def setSharpness(self, caller=""):

		if (not config.plugins.autosharpness.enabled.value):
			log("%sDaemon.setSharpness() plugin disabled; returning" % caller)
			self.previousStreamRes = "Unknown"
			return
			
		log("%sDaemon.setSharpness() starting with previousStreamRes=%s" % (caller, self.previousStreamRes))
		log("%sDaemon.setSharpness() config: %s" % (caller, Daemon.instance.getConfigString()))

		service = self.session.nav.getCurrentService()
		if not service:
			log("%sDaemon.setSharpness() couldn't get current service; returning" % caller)
			return
		info = service.info()
		if not info:
			log("%sDaemon.setSharpness() couldn't get service info; returning" % caller)
			return

		
		streamHeight = int(info.getInfo(iServiceInformation.sVideoHeight))
		streamWidth = int(info.getInfo(iServiceInformation.sVideoWidth))
		streamProgressive = int(info.getInfo(iServiceInformation.sProgressive))
		streamFramerate = int(info.getInfo(iServiceInformation.sFrameRate))
								
		if (0 < streamHeight <= 3840) and (0 < streamWidth <= 4096): # 2160x3840 vertical
			log("%sDaemon.setSharpness() got stream res from service info" % caller)	
		else:
			def getInfoFromProc(pathname, base=10):
				info = None
				if os.path.exists(pathname):
					f = open(pathname, "r")
					try:
						val = int(f.read(), base)
						if val >= 0:
							info = val
					except:
						log("%sDaemon.setSharpness() failed to read from %s" % (caller, pathname))
					f.close()
				else:
					log("%sDaemon.setSharpness() path not found: %s" % (caller, pathname))
					return
				return info
			
			log("%sDaemon.setSharpness() no service info; trying proc instead" % caller)
			streamHeight = getInfoFromProc("/proc/stb/vmpeg/0/yres", 16)
			streamWidth = getInfoFromProc("/proc/stb/vmpeg/0/xres", 16)
			streamProgressive = getInfoFromProc("/proc/stb/vmpeg/0/progressive")
			streamFramerate = getInfoFromProc("/proc/stb/vmpeg/0/framerate")
			
			if not (isinstance(streamHeight, int) and isinstance(streamWidth, int) and
					isinstance(streamProgressive, int) and 
					(0 < streamHeight <= 3840) and (0 < streamWidth <= 4096)): # 2160x3840 vertical
					log("%sDaemon.setSharpness() failed to get stream res from proc; returning" % caller)
					return

		
		
		streamRes = "Unknown"; newSharpness = 0; detectionMethod = "Nearest" # Nearest / Minimum
		
		# Nearest: matches the video stream resolution with the nearest resolution in: 480i/p, 576i/p,
		# 720p, 1080i/p, 2160p.
		# 
		# Minimum: same as Nearest, but matches it to the minimum which won't result in resolution
		# loss.
		#
		# eg. Nearest will match 852x480 with 480p, but Minimum will match it with 720p, since 480p
		# is 720x480 and would result in horizontal loss of resolution.  Nearest is more suitable for
		# approximating the amount of resolution; Minimum is more suitable for auto res switching.
		#
		# The code has been tested with the following resolutions: 3840x2160, 3840x2080, 3840x1600,
		# 2880x2160, 2560x2160, 2560x1440, 2560x1392, 2560x1072, 1920x1440, 1712x1440, 1920x1200,
		# 1600x1200, 1920x1080, 1920x1088, 1920x1040, 1920x800, 1440x1080, 1440x1088, 1280x1080,
		# 1280x1088, 1680x1050, 1600x1024, 1600x900, 1366x768, 1280x1024, 1280x960, 1280x800, 1280x768,
		# 1152x864, 1024x768, 1280x720, 1280x692, 1280x544, 960x720, 854x720, 854x480, 854x464, 854x368,
		# 1024x576, 768x576, 1024x560, 1024x432, 800x600, 720x480, 700x480, 640x480, 720x576, 700x576,
		# Vertical videos: 406x720, 608x1080, 810x1440, 1216x2160, 2160x3840 
		#
		# Test script: https://pastebin.com/3rpX4369

		if (detectionMethod == "Nearest") and (streamWidth >= streamHeight):		
			verticalVideo = False		
			
			if (streamWidth > 2560) or (streamHeight > 1440):
				streamRes, newSharpness = "2160p", int(config.plugins.autosharpness.sharpness_2160p.value)	
			elif ((streamWidth >= 1600) or (streamHeight >= 900)) and (streamProgressive != 0):
				streamRes, newSharpness = "1080p", int(config.plugins.autosharpness.sharpness_1080p.value)
			elif ((streamWidth >= 1600) or (streamHeight >= 900)) and (streamProgressive == 0):
				streamRes, newSharpness = "1080i", int(config.plugins.autosharpness.sharpness_1080i.value)	
			elif (streamWidth > 1024) or (streamHeight >= 720):
				streamRes, newSharpness = "720p", int(config.plugins.autosharpness.sharpness_720p.value)
			elif ((streamWidth > 864) or (streamHeight > 480)) and (streamProgressive != 0):
				streamRes, newSharpness = "576p", int(config.plugins.autosharpness.sharpness_480p576p.value)
			elif ((streamWidth > 864) or (streamHeight > 480)) and (streamProgressive == 0):
				streamRes, newSharpness = "576i", int(config.plugins.autosharpness.sharpness_480i576i.value)
			elif (streamHeight <= 480) and (streamProgressive != 0):
				streamRes, newSharpness = "480p", int(config.plugins.autosharpness.sharpness_480p576p.value)
			elif (streamHeight <= 480) and (streamProgressive == 0):
				streamRes, newSharpness = "480i", int(config.plugins.autosharpness.sharpness_480i576i.value)
		
		elif (detectionMethod == "Nearest") and (streamWidth < streamHeight):		
			verticalVideo = True		
			
			if (streamHeight > 1440):
				streamRes, newSharpness = "2160p", int(config.plugins.autosharpness.sharpness_2160p.value)
			elif (streamHeight >= 900) and (streamProgressive != 0):
				streamRes, newSharpness = "1080p", int(config.plugins.autosharpness.sharpness_1080p.value)
			elif (streamHeight >= 900) and (streamProgressive == 0):
				streamRes, newSharpness = "1080i", int(config.plugins.autosharpness.sharpness_1080i.value)			
			elif (streamHeight >= 656):
				streamRes, newSharpness = "720p", int(config.plugins.autosharpness.sharpness_720p.value)			
			elif (streamHeight > 480) and (streamProgressive != 0):
				streamRes, newSharpness = "576p", int(config.plugins.autosharpness.sharpness_480p576p.value)
			elif (streamHeight > 480) and (streamProgressive == 0):
				streamRes, newSharpness = "576i", int(config.plugins.autosharpness.sharpness_480i576i.value)
			elif (streamHeight <= 480) and (streamProgressive != 0):
				streamRes, newSharpness = "480p", int(config.plugins.autosharpness.sharpness_480p576p.value)
			elif (streamHeight <= 480) and (streamProgressive == 0):
				streamRes, newSharpness = "480i", int(config.plugins.autosharpness.sharpness_480i576i.value)
	
		elif (detectionMethod == "Minimum") and (streamWidth >= streamHeight):
			verticalVideo = False		
			
			if (streamWidth > 1920) or (streamHeight > 1088):
				streamRes, newSharpness = "2160p", int(config.plugins.autosharpness.sharpness_2160p.value)
			elif ((streamWidth > 1280) or (streamHeight > 720)) and (streamProgressive != 0):
				streamRes, newSharpness = "1080p", int(config.plugins.autosharpness.sharpness_1080p.value)
			elif ((streamWidth > 1280) or (streamHeight > 720)) and (streamProgressive == 0):
				streamRes, newSharpness = "1080i", int(config.plugins.autosharpness.sharpness_1080i.value)
			elif (streamWidth > 720):
				streamRes, newSharpness = "720p", int(config.plugins.autosharpness.sharpness_720p.value)
			elif (streamHeight > 480) and (streamProgressive != 0):
				streamRes, newSharpness = "576p", int(config.plugins.autosharpness.sharpness_480p576p.value)
			elif (streamHeight > 480) and (streamProgressive == 0):
				streamRes, newSharpness = "576i", int(config.plugins.autosharpness.sharpness_480i576i.value)
			elif (streamHeight <= 480) and (streamProgressive != 0):
				streamRes, newSharpness = "480p", int(config.plugins.autosharpness.sharpness_480p576p.value)
			elif (streamHeight <= 480) and (streamProgressive == 0):
				streamRes, newSharpness = "480i", int(config.plugins.autosharpness.sharpness_480i576i.value)
	
		elif (detectionMethod == "Minimum") and (streamWidth < streamHeight):		
			verticalVideo = True		
			
			if (streamHeight > 1088):
				streamRes, newSharpness = "2160p", int(config.plugins.autosharpness.sharpness_2160p.value)
			elif (streamHeight > 720) and (streamProgressive != 0):
				streamRes, newSharpness = "1080p", int(config.plugins.autosharpness.sharpness_1080p.value)
			elif (streamHeight > 720) and (streamProgressive == 0):
				streamRes, newSharpness = "1080i", int(config.plugins.autosharpness.sharpness_1080i.value)			
			elif (streamHeight > 576):
				streamRes, newSharpness = "720p", int(config.plugins.autosharpness.sharpness_720p.value)			
			elif (streamHeight > 480) and (streamProgressive != 0):
				streamRes, newSharpness = "576p", int(config.plugins.autosharpness.sharpness_480p576p.value)
			elif (streamHeight > 480) and (streamProgressive == 0):
				streamRes, newSharpness = "576i", int(config.plugins.autosharpness.sharpness_480i576i.value)
			elif (streamHeight <= 480) and (streamProgressive != 0):
				streamRes, newSharpness = "480p", int(config.plugins.autosharpness.sharpness_480p576p.value)
			elif (streamHeight <= 480) and (streamProgressive == 0):
				streamRes, newSharpness = "480i", int(config.plugins.autosharpness.sharpness_480i576i.value)
			
		
		if (streamRes == "Unknown"):
			log("%sDaemon.setSharpness() failed to infer resolution from w=%s, h=%s, p=%s, v=%s; returning" \
				% (caller, streamWidth, streamHeight, streamProgressive, verticalVideo))
			return
		else:
			log("%sDaemon.setSharpness() inferred %s from w=%s, h=%s, p=%s, v=%s" \
				% (caller, streamRes, streamWidth, streamHeight, streamProgressive, verticalVideo))			
			
		
		applyBy = str(config.plugins.autosharpness.applyby.value)
		applyDiscreetly = str(config.plugins.autosharpness.applydiscreetly.value)
		applySuccess = False
		
		if 	((applyDiscreetly == "No") or 
			(applyDiscreetly == "Yes" and streamRes != self.previousStreamRes) or
			(self.getEnforceFrequency("Config") != "No")):
								
			if (applyBy == "Config") or (applyBy == "Config+proc"):
				try: 
					config.pep.sharpness.value = newSharpness
					config.pep.sharpness.save()
					applySuccess = True
					log("%sDaemon.setSharpness() wrote %s to config.pep.sharpness, which now contains: %s" \
						% (caller, newSharpness, str(config.pep.sharpness.value)))				
				except:
					log("%sDaemon.setSharpness() failed writing %s to config.pep.sharpness" % (caller, newSharpness))
							
			if (applyBy == "Proc") or (applyBy == "Config+proc"):

				if os.path.exists("/proc/stb/vmpeg/0/pep_sharpness"):
					try:
						val = int(newSharpness * 256)
						f = open("/proc/stb/vmpeg/0/pep_sharpness", "w")
						f.write("%0.8X" % val)
						f.close()
						applySuccess = True
						log("%sDaemon.setSharpness() wrote %0.8X to proc/stb/vmpeg/0/pep_sharpness" % (caller, val))
					except IOError:
						log("%sDaemon.setSharpness() failed writing to proc/stb/vmpeg/0/pep_sharpness; returning" % caller) 
						return
				else:
					log("%sDaemon.setSharpness() path not found: proc/stb/vmpeg/0/pep_sharpness; returning" % caller) 
					return
						
				
				if os.path.exists("/proc/stb/vmpeg/0/pep_apply"):	
					try:
						# time.sleep(0.1) ?
						f = open("/proc/stb/vmpeg/0/pep_apply", "w")
						f.write("1")
						f.close()
						log("%sDaemon.setSharpness() wrote 1 to proc/stb/vmpeg/0/pep_apply" % caller)
					except IOError:
						log("%sDaemon.setSharpness() failed writing to /proc/stb/vmpeg/0/pep_apply; " \
							"continuing anyway" % caller)
				else:
					log("%sDaemon.setSharpness() path not found: proc/stb/vmpeg/0/pep_apply; " \
						"continuing anyway" % caller)
								
			
			if (applySuccess):			
				self.notificationLabel.hide()
				self.notificationLabel["resolution"].setText("Video content: %s" % streamRes)
				self.notificationLabel["sharpness"].setText("Sharpness set to: %s" % newSharpness)			
				if 	((config.plugins.autosharpness.label.value != "No") and
					(not GUI.isOpen) and (caller != "Daemon.enforceSharpness() ")):
					log("%sDaemon.setSharpness() notificationLabel.show()" % caller)
					self.notificationLabel.show()	
							
		else:
			log("%sDaemon.setSharpness() skipped setting sharpness (applyDiscreetly=Yes and streamRes=previousStreamRes)" % caller)
			
		
		self.previousStreamRes = streamRes
		
		if 	((GUI.isOpen) and (GUI.instance != None) and
			(caller != "GUI.changedEntry() ") and (caller != "GUI.keyGreenConfirm() ")):			
			log("%sDaemon.setSharpness() refreshing GUI" % caller)
			GUI.instance.createConfig("%sDaemon.setSharpness() " % caller) 
			# also calls GUI.selectionChanged() if cursor happens to be on a GUI element
			# that was changed as a result of GUI.createConfig()
			
		if	((GUI_SharpnessSetter.isOpen) and (GUI_SharpnessSetter.instance != None) and
			(caller != "Daemon.enforceSharpness() ")):		
			GUI_SharpnessSetter.instance.keyRed("%sDaemon.setSharpness() " % caller)
	
		log("%sDaemon.setSharpness() finish" % caller)

	
def log(line):
	
	enableLogging = True
	logTarget = "Var" # File/Var
	
	if (logTarget == "File"):
	
		logFile = os.path.dirname(os.path.abspath(__file__)) + "/log.log"
		try:
			if (enableLogging == True):
				f = open(logFile, "a")
				f.write(datetime.now().strftime("%H:%M:%S") + "  " + line + "\n") #%f
				f.close()
			else:
				os.remove(logFile)
		except:
			pass
			
	elif (logTarget == "Var"):
	
		Daemon.log.append(datetime.now().strftime("%H:%M:%S") + "  " + line)


def startDaemon(session, **kwargs):	
	# if os.path.exists(logfile):
		# os.remove(logfile)
	log("*************")
	log("startDaemon()")
	session.open(Daemon)

	
def startGUI(session, **kwargs):
	log("startGUI()")
	session.open(GUI)

	
def Plugins(**kwargs):			
	DescriptorList = []   
	DescriptorList.append(
		PluginDescriptor(
			name="AutoSharpness Daemon",		
			where = PluginDescriptor.WHERE_SESSIONSTART,		
			description=_("AutoSharpness daemon"),
			fnc=startDaemon,
			needsRestart=True
		)	
	)	
	DescriptorList.append(
        PluginDescriptor(
			name="AutoSharpness",		
			#where = PluginDescriptor.WHERE_PLUGINMENU,
			where = [
					PluginDescriptor.WHERE_PLUGINMENU,
					PluginDescriptor.WHERE_EXTENSIONSMENU
					],
            description=_("AutoSharpness GUI"),
            fnc=startGUI
		)		
	)	
	return DescriptorList
			

