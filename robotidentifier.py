#!/usr/bin/python
from __future__ import print_function
from config import *
from utils.darknet_classify_image import *
from utils.keras_classify_image import *
from utils.azure_ocr import *
from utils.tesseract_ocr import *
import utils.logger as logger
from utils.rotate import *
from utils.lookup_database import *
import sys
from PIL import Image
import time
import os
from RotNet.correct_rotation import *

PYTHON_VERSION = sys.version_info[0]
OS_VERSION = os.name

class RobotIdentifier():
	''' Programatically finds and determines if a pictures contains an asset and where it is. '''

	def init_vars(self):
		try:
			self.DARKNET = DARKNET
			self.KERAS = KERAS
			self.TESSERACT = TESSERACT
			self.COGNITIVE_SERVICES = COGNITIVE_SERVICES
			return 0
		except:
			return -1

	def init_classifier(self):
		''' Initializes the classifier '''
		try:
			if self.DARKNET:
			# Get a child process for speed considerations
				logger.good("Initializing Darknet")
				self.classifier = DarknetClassifier()
			elif self.KERAS:
				logger.good("Initializing Keras")
				self.classifier = KerasClassifier()
			if self.classifier == None or self.classifier == -1:
				return -1
			return 0
		except:
			return -1

	def init_ocr(self):
		''' Initializes the OCR engine '''
		try:
			if self.TESSERACT:
				logger.good("Initializing Tesseract")
				self.OCR = TesseractOCR()
			elif self.COGNITIVE_SERVICES:
				logger.good("Initializing Cognitive Services")
				self.OCR = AzureOCR()
			if self.OCR == None or self.OCR == -1:
				return -1
			return 0
		except:
			return -1

	def init_tabComplete(self):
		''' Initializes the tab completer '''
		try:
			if OS_VERSION == "posix":
				global tabCompleter
				global readline
				from utils.PythonCompleter import tabCompleter
				import readline
				comp = tabCompleter()
				# we want to treat '/' as part of a word, so override the delimiters
				readline.set_completer_delims(' \t\n;')
				readline.parse_and_bind("tab: complete")
				readline.set_completer(comp.pathCompleter)
				if not comp:
					return -1
			return 0
		except:
			return -1

	def prompt_input(self):
		''' Prompts the user for input, depending on the python version.
		Return: The filename provided by the user. '''
		if PYTHON_VERSION == 3:
			filename = str(input(" Specify File >>> "))
		elif PYTHON_VERSION == 2:
			filename = str(raw_input(" Specify File >>> "))
		return filename

	from utils.locate_asset import locate_asset

	def __init__(self):
		''' Run RobotIdentifier! '''

		if self.init_vars() != 0:
			fatal("Init vars")
		if self.init_tabComplete() != 0:
			fatal("Init tabcomplete")
		if self.init_classifier() != 0:
			fatal("Init Classifier")
		if self.init_ocr() != 0:
			fatal("Init OCR")
		if initialize_rotnet() != 0:
			fatal("Init RotNet")

		while True:

			filename = self.prompt_input()
			start = time.time()

			#### Classify Image ####
			logger.good("Classifying Image")
			coords = self.classifier.classify_image(filename)
			########################

			time1 = time.time()
			print("Classify Time: " + str(time1-start))

			#### Crop/rotate Image ####
			logger.good("Locating Asset")
			cropped_images = self.locate_asset(filename, self.classifier, lines=coords)
			###########################
			
			time2 = time.time()
			print("Rotate Time: " + str(time2-time1))

			#### Perform OCR ####
			ocr_results = None
			if cropped_images == []:
				logger.bad("No assets found, so terminating execution")	 
			else:
				logger.good("Performing OCR")
				ocr_results = self.OCR.ocr(cropped_images)
			#####################
			
			time3 = time.time()
			print("OCR Time: " + str(time3-time2))

			#### Lookup Database ####
			lookup_database(ocr_results)
			#########################

			end = time.time()
			logger.good("Elapsed: " + str(end-start))

if __name__ == "__main__":
	RobotIdentifier()
