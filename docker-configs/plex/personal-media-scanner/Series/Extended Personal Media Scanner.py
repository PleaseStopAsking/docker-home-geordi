# Version Date: 2021-07-03

import re, os, os.path, datetime, ConfigParser
import Media, VideoFiles, Stack, Utils
from mp4file import mp4file, atomsearch

def log(methodName, message, *args):
    '''
        Create a log message given the message and arguments
    '''
    logMsg = ''
    # Replace the arguments in the string
    if args:
        logMsg = message % args
        
    logMsg = methodName + ' :: ' + logMsg
    print(logMsg)

class CustomParserConfig(object):
    '''
        Finds the configuration for the specified file
    '''
    
    def __init__(self, filePath):
        self.filePath = filePath
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(filePath)
        
    def fileNameRegex(self):
        return self.config.get('parser', 'file.name.regex')

class ConfigMap(object):
    
    def findCustomParser(self, rootDir, filePath):
        customParser = None
        
        configFile = self.findConfigFile(rootDir, filePath)
        if configFile is not None:
            log('__init__', 'found config file %s for media file %s', configFile, filePath)
            # Create the config
            config = CustomParserConfig(configFile)
            # and custom parser
            customParser = CustomMediaParser(config)
            
        return customParser
             
    def findConfigFile(self, rootDir, filePath):
        rootDirFound = False
        parentDir = filePath
        
        # iterate over the directory
        while not rootDirFound:
            # Get the parent directory for the file
            parentDir = os.path.dirname(parentDir)

            log('findConfigFile', 'looking in parent directory %s', parentDir)
            # create the file path
            configFilePath = os.path.normcase(parentDir + '/ext-media.config')
            log('findConfigFile', 'determining whether config file %s exists', configFilePath)
            if os.path.exists(configFilePath) and os.path.isfile(configFilePath):
                log('findConfigFile', 'config file %s exists', configFilePath)
                return configFilePath

            # check to see if this is the root dir
            if parentDir == rootDir:
                rootDirFound = True           
            
class BaseMediaParser(object):
    '''
        Parses the file name and determines the type of tile that was found
    '''

    # Episode name REGEX
    partRegexes = [
                    r'(?P<episodeTitle>.+)(\.[ ]*|-[ ]*)(part[0-9]+|pt[0-9]+)',
                    r'(?P<episodeTitle>.+)([ ]+)(part[0-9]+|pt[0-9]+)'
                    ]

    def __init__(self):
        self.showTitle = None
        self.seasonNumber = None
        self.seasonYear = None
        self.episodeTitle = None
        self.episodeNumber = None
        
    def stripPart(self, episodeTitle):
        processed = episodeTitle
        # Test whether it contains part
        for partRegex in self.partRegexes:
            match = re.search(partRegex, processed)
            if match:
                log('stripPart', 'episode title %s contains part', processed)
                processed = match.group('episodeTitle').strip()
                log('stripPart', 'stripped episode title: %s', processed)
                break
                
        return processed

    def scrub(self, string):
        processed = ''
        matches = re.split(r'[\.\-_]+', string)
        idx = 1
        if matches is not None:
            for match in matches:
                processed = processed + match
                if idx < len(matches):
                    processed = processed + ' '
                idx = idx + 1
        else:
            processed = string
            
        log('scrubString', 'original: [%s] scrubbed: [%s]', string, processed)
        return processed
    
    def setValues(self, match):
        # set the show title
        self.showTitle = self.scrub(match.group('showTitle').strip())

        # get the episode title
        self.episodeTitle = self.scrub(self.stripPart(match.group('episodeTitle').strip()))

    def getSupportedRegexes(self):
        return []
    
    def containsMatch(self, mediaFile):
        retVal = False
        # Iterate over the list of regular expressions
        for regex in self.getSupportedRegexes():
            # Find out what file format is being used
            match = re.search(regex, mediaFile, re.IGNORECASE)
            if match:
                retVal = True
                break
            
        return retVal
        

    def parse(self, mediaFile, lang):
        self.mediaFile = mediaFile
        self.lang = lang

        # Iterate over the list of regular expressions
        for regex in self.getSupportedRegexes():
            # Find out what file format is being used
            match = re.search(regex, mediaFile, re.IGNORECASE)
            log('parse', 'regex %s - matches: %s', regex, match)
            if match:
                log('parse', 'found matches')
                self.setValues(match)
                break
    
    def getShowTitle(self):
        return self.showTitle

    def getSeasonNumber(self):
        return self.seasonNumber

    def getSeasonYear(self):
        return self.seasonYear
        
    def getEpisodeTitle(self):
        return self.episodeTitle

    def getEpisodeNumber(self):
        return self.episodeNumber

class BaseDatedSeriesMediaParser(BaseMediaParser):

    def __init__(self):
        BaseMediaParser.__init__(self)
        self.episodeYear = None
        self.episodeMonth = None
        self.episodeDay = None
        self.episodeReleaseDate = None

    def setValues(self, match):
        # set the common values
        BaseMediaParser.setValues(self, match)

        # set the season number
        if 'seasonNumber' in match.groupdict():
            self.seasonNumber = int(match.group('seasonNumber').strip())

        # set the episode year
        if 'episodeYear' in match.groupdict():
            self.episodeYear = int(match.group('episodeYear').strip())

        # if the regex did not contain a season number use the episode year
        if self.seasonNumber is None and self.episodeYear is not None:
            self.seasonNumber = self.episodeYear
        # if the regex did not contain an episode year use the season number
        if self.episodeYear is None and self.seasonNumber is not None:
            self.episodeYear = self.seasonNumber

        # get month and day values
        self.episodeMonth = int(match.group('episodeMonth').strip())
        self.episodeDay = int(match.group('episodeDay').strip())
        log('setValues', 'parsed date: year %s month %s day %s', self.episodeYear, self.episodeMonth, self.episodeDay)
        # Create the episode release date
        self.episodeReleaseDate = datetime.datetime(self.episodeYear, self.episodeMonth, self.episodeDay)
        log('setValues', 'episode date: %s', str(self.episodeReleaseDate))

class SeriesDateBasedMediaParser(BaseDatedSeriesMediaParser):
    
    def __init__(self):
        BaseDatedSeriesMediaParser.__init__(self)

    def getSupportedRegexes(self):
        return [
                # \Show Title\2012 - Season Title\Show Title - 2012-09-19 - Episode Title.mp4
                # \Show Title\2012 - Season Title\2012-09-19 - Episode Title.mp4    
                # \Show Title\2012\Show Title - 2012-09-19 - Episode Title.mp4
                # \Show Title\2012\2012-09-19 - Episode Title.mp4
                r'[\\/](?P<showTitle>[^\\/]+)[\\/](?P<seasonNumber>[1-2][0-9][0-9][0-9])([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[\\/][^\\/]*?(?P<episodeYear>[1-2][0-9][0-9][0-9])[-\. ]{0,1}(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])(_(?P<episodeIndex>[0-9]+)){0,2}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$' , 
                # \2012 - Season Title\Show Title\Show Title - 2012-09-19 - Episode Title.mp4
                # \2012 - Season Title\Show Title\2012-09-19 - Episode Title.mp4    
                # \2012\Show Title\Show Title - 2012-09-19 - Episode Title.mp4
                # \2012\Show Title\2012-09-19 - Episode Title.mp4
                r'[\\/](?P<seasonNumber>[1-2][0-9][0-9][0-9])([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[\\/](?P<showTitle>[^\\/]+)[\\/][^\\/]*?(?P<episodeYear>[1-2][0-9][0-9][0-9])[-\. ]{0,1}(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])(_(?P<episodeIndex>[0-9]+)){0,2}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$' , 
                # \Show Title\2012 - Season Title\Show Title - 09-19-2013 - Episode Title.mp4
                # \Show Title\2012 - Season Title\09-19-2013 - Episode Title.mp4
                # \Show Title\2012\Show Title - 09-19-2013 - Episode Title.mp4
                # \Show Title\2012\09-19-2013 - Episode Title.mp4
                r'[\\/](?P<showTitle>[^\\/]+)[\\/](?P<seasonNumber>[1-2][0-9][0-9][0-9])([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[\\/][^\\/]*?(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. ]{0,1}(?P<episodeYear>[1-2][0-9][0-9][0-9])(_(?P<episodeIndex>[0-9]+)){0,2}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$' , 
                # \2012 - Season Title\Show Title\Show Title - 09-19-2013 - Episode Title.mp4
                # \2012 - Season Title\Show Title\09-19-2013 - Episode Title.mp4
                # \2012\Show Title\Show Title - 09-19-2013 - Episode Title.mp4
                # \2012\Show Title\09-19-2013 - Episode Title.mp4
                r'[\\/](?P<seasonNumber>[1-2][0-9][0-9][0-9])([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[\\/](?P<showTitle>[^\\/]+)[\\/][^\\/]*?(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. ]{0,1}(?P<episodeYear>[1-2][0-9][0-9][0-9])(_(?P<episodeIndex>[0-9]+)){0,2}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$' , 
                # \Show Title\2012\Show Title - 09-19 - Episode Title.mp4
                # \Show Title\2012\09-19 - Episode Title.mp4
                r'[\\/](?P<showTitle>[^\\/]+)[\\/](?P<seasonNumber>[1-2][0-9][0-9][0-9])([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[\\/][^\\/e]*?(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])(_(?P<episodeIndex>[0-9]+)){0,2}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
                # \2012\Show Title\Show Title - 09-19 - Episode Title.mp4
                # \2012\Show Title\09-19 - Episode Title.mp4
                r'[\\/](?P<seasonNumber>[1-2][0-9][0-9][0-9])([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[\\/](?P<showTitle>[^\\/]+)[\\/][^\\/e]*?(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])(_(?P<episodeIndex>[0-9]+)){0,2}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
                # \Show Title\2012-09-19_23 - Episode Title.mp4
                # \Show.Title\2012.09.19_23.Episode.Title.mp4
                r'[\\/](?P<showTitle>[^\\/]+)[\\/](?P<seasonNumber>[1-2][0-9][0-9][0-9])([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[-\. ]{0,1}(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])(_(?P<episodeIndex>[0-9]+)){0,2}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
                # \Show Title - 2012-09-19_23 - Episode Title.mp4
                # \Show.Title.2012.09.19_23.Episode.Title.mp4
                r'[\\/](?P<showTitle>[^\\/]+?)[ ]*[-\.]{0,1}[ ]*(?P<episodeYear>[1-2][0-9][0-9][0-9])[-\. ]{0,1}(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])(_(?P<episodeIndex>[0-9]+)){0,2}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
                # \Show Title - 09-19-2012_23 - Episode Title.mp4
                # \Show.Title.09.19.2012_23.Episode.Title.mp4
                r'[\\/](?P<showTitle>[^\\/]+?)[ ]*[-\.]{0,1}[ ]*(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. ]{0,1}(?P<episodeYear>[1-2][0-9][0-9][0-9])(_(?P<episodeIndex>[0-9]+)){0,2}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$'
            ]
                
    def setValues(self, match):
        # set the common values
        BaseDatedSeriesMediaParser.setValues(self, match)
        
        # compute the episode index using the episode's day of year and index values
        dayOfYear = str(self.episodeReleaseDate.timetuple().tm_yday)
        # append the index number
        episodeIndex = 1
        if 'episodeIndex' in match.groupdict() and match.group('episodeIndex') is not None:
            episodeIndex = int(match.group('episodeIndex').strip())
            log('setValues', 'episode contains index %s', episodeIndex)
        episodeIndexAsString = format(episodeIndex, '02')
        self.episodeNumber = int(dayOfYear + str(episodeIndexAsString))
        log('setValues', 'episode number %s', self.episodeNumber)

class SeriesDateTimeBasedMediaParser(BaseDatedSeriesMediaParser):
    
    def __init__(self):
        BaseDatedSeriesMediaParser.__init__(self)

        self.episodeHour = None
        self.episodeMinute = None
        self.episodeSecond = None
        self.episodeAMPM = None

    def getSupportedRegexes(self):
        return [
                # \2012\02\2012-02-19 13 00 00 - Episode Title.mp4
                # \2012\02\2012-02-19 13-00-00 - Episode Title.mp4
                # \2013\03\2013.03.19_01.00.00.AM - Episode Title.mp4
                r'[\\/](?P<showTitle>[1-2][0-9][0-9][0-9])[\\/](?P<seasonNumber>[0-9]{2})[\\/][^\\/]*?(?P<episodeYear>[1-2][0-9][0-9][0-9])[-\. ]{0,1}(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. _](?P<episodeHour>[0-9]{2})[-\. ]{0,1}(?P<episodeMinute>[0-9]{2})[-\. ]{0,1}(?P<episodeSecond>[0-9]{2})[-\. ]{0,1}(?P<episodeAMPM>[AM|PM]{2}){0,1}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$' , 
                # \Show Title\2012 - Season Title\Show Title - 2012-09-19 13 00 00 - Episode Title.mp4
                # \Show Title\2012 - Season Title\2012-09-19 13 00 00 - Episode Title.mp4    
                # \Show Title\2012\Show Title - 2012-09-19_13-00-00 - Episode Title.mp4
                # \Show Title\2012\2012-09-19 13 00 00 - Episode Title.mp4
                r'[\\/](?P<showTitle>[^\\/]+)[\\/](?P<seasonNumber>[1-2][0-9][0-9][0-9])([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[\\/][^\\/]*?(?P<episodeYear>[1-2][0-9][0-9][0-9])[-\. ]{0,1}(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. _](?P<episodeHour>[0-9]{2})[-\. ]{0,1}(?P<episodeMinute>[0-9]{2})[-\. ]{0,1}(?P<episodeSecond>[0-9]{2})[-\. ]{0,1}(?P<episodeAMPM>[AM|PM]{2}){0,1}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$' , 
                # \2012 - Season Title\Show Title\Show Title - 2012-09-19.13-00-00 - Episode Title.mp4
                # \2012 - Season Title\Show Title\2012-09-19_13-00-00 - Episode Title.mp4    
                # \2012\Show Title\Show Title - 2012-09-19 13 00 00 - Episode Title.mp4
                # \2012\Show Title\Show Title - 2012.09.19.07.01.01.AM - Episode Title.mp4
                # \2012\Show Title\2012-09-19 13 00 00 - Episode Title.mp4
                r'[\\/](?P<seasonNumber>[1-2][0-9][0-9][0-9])([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[\\/](?P<showTitle>[^\\/]+)[\\/][^\\/]*?(?P<episodeYear>[1-2][0-9][0-9][0-9])[-\. ]{0,1}(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. _](?P<episodeHour>[0-9]{2})[-\. ]{0,1}(?P<episodeMinute>[0-9]{2})[-\. ]{0,1}(?P<episodeSecond>[0-9]{2})[-\. ]{0,1}(?P<episodeAMPM>[AM|PM]{2}){0,1}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$' , 
                # \Show Title\2012 - Season Title\Show Title - 09-19-2013 13 00 00 - Episode Title.mp4
                # \Show Title\2012 - Season Title\09-19-2013 13 00 00 - Episode Title.mp4
                # \Show Title\2012 - Season Title\09-19-2013 01-01-00-AM - Episode Title.mp4
                # \Show Title\2012\Show Title - 09-19-2013 13 00 00 - Episode Title.mp4
                # \Show Title\2012\09-19-2013 13 00 00 - Episode Title.mp4
                r'[\\/](?P<showTitle>[^\\/]+)[\\/](?P<seasonNumber>[1-2][0-9][0-9][0-9])([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[\\/][^\\/]*?(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. ]{0,1}(?P<episodeYear>[1-2][0-9][0-9][0-9])[-\. _](?P<episodeHour>[0-9]{2})[-\. ]{0,1}(?P<episodeMinute>[0-9]{2})[-\. ]{0,1}(?P<episodeSecond>[0-9]{2})[-\. ]{0,1}(?P<episodeAMPM>[AM|PM]{2}){0,1}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$' , 
                # \2012 - Season Title\Show Title\Show Title - 09-19-2013 13 00 00 - Episode Title.mp4
                # \2012 - Season Title\Show Title\09-19-2013 13 00 00 - Episode Title.mp4
                # \2012\Show Title\Show Title - 09-19-2013 13 00 00 - Episode Title.mp4
                # \2012\Show Title\09-19-2013 13 00 00 - Episode Title.mp4
                # \2012\Show Title\09.19.2013_10.00.00.AM - Episode Title.mp4
                r'[\\/](?P<seasonNumber>[1-2][0-9][0-9][0-9])([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[\\/](?P<showTitle>[^\\/]+)[\\/][^\\/]*?(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. ]{0,1}(?P<episodeYear>[1-2][0-9][0-9][0-9])[-\. _](?P<episodeHour>[0-9]{2})[-\. ]{0,1}(?P<episodeMinute>[0-9]{2})[-\. ]{0,1}(?P<episodeSecond>[0-9]{2})[-\. ]{0,1}(?P<episodeAMPM>[AM|PM]{2}){0,1}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$' , 
                # \Show Title\2012\Show Title - 09-19 13 00 00 - Episode Title.mp4
                # \Show Title\2012\09-19 13 00 00 - Episode Title.mp4
                # \Show Title\2012\09-19 09-03-00-AM - Episode Title.mp4
                r'[\\/](?P<showTitle>[^\\/]+)[\\/](?P<seasonNumber>[1-2][0-9][0-9][0-9])([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[\\/][^\\/e]*?(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. _](?P<episodeHour>[0-9]{2})[-\. ]{0,1}(?P<episodeMinute>[0-9]{2})[-\. ]{0,1}(?P<episodeSecond>[0-9]{2})[-\. ]{0,1}(?P<episodeAMPM>[AM|PM]{2}){0,1}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
                # \2012\Show Title\Show Title - 09-19 13 00 00 - Episode Title.mp4
                # \2012\Show Title\09-19 13 00 00 - Episode Title.mp4
                # \2012\Show Title\09-19_12.14.15.AM - Episode Title.mp4
                r'[\\/](?P<seasonNumber>[1-2][0-9][0-9][0-9])([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[\\/](?P<showTitle>[^\\/]+)[\\/][^\\/e]*?(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. _](?P<episodeHour>[0-9]{2})[-\. ]{0,1}(?P<episodeMinute>[0-9]{2})[-\. ]{0,1}(?P<episodeSecond>[0-9]{2})[-\. ]{0,1}(?P<episodeAMPM>[AM|PM]{2}){0,1}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
                # \Show Title - 2012-09-19_23 13 00 - Episode Title.mp4
                # \Show.Title.2012.09.19-23.13.00.Episode.Title.mp4
                r'[\\/](?P<showTitle>[^\\/]+?)[ ]*[-\.]{0,1}[ ]*(?P<episodeYear>[1-2][0-9][0-9][0-9])[-\. ]{0,1}(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. _](?P<episodeHour>[0-9]{2})[-\. ]{0,1}(?P<episodeMinute>[0-9]{2})[-\. ]{0,1}(?P<episodeSecond>[0-9]{2})[-\. ]{0,1}(?P<episodeAMPM>[AM|PM]{2}){0,1}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
                # \Show Title - 09-19-2012_09-39-23 - Episode Title.mp4
                # \Show.Title.09.19.2012 23.34.30.Episode.Title.mp4
                r'[\\/](?P<showTitle>[^\\/]+?)[ ]*[-\.]{0,1}[ ]*(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. ]{0,1}(?P<episodeYear>[1-2][0-9][0-9][0-9])[-\. _](?P<episodeHour>[0-9]{2})[-\. ]{0,1}(?P<episodeMinute>[0-9]{2})[-\. ]{0,1}(?P<episodeSecond>[0-9]{2})[-\. ]{0,1}(?P<episodeAMPM>[AM|PM]{2}){0,1}[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$'
            ]

    def setValues(self, match):
        # set the common values
        BaseDatedSeriesMediaParser.setValues(self, match)

        # parse the hour parts
        self.episodeHour = int(match.group('episodeHour').strip())
        self.episodeAMPM = match.group('episodeAMPM')
        self.episodeMinute = int(match.group('episodeMinute').strip())
        self.episodeSecond = int(match.group('episodeSecond').strip())
        log('setValues', 'parsed time: hour %s minute %s second %s AM/PM %s', self.episodeHour, self.episodeMinute, self.episodeSecond, self.episodeAMPM)
        # if the regex contains PM then add 12 hours to episode
        if self.episodeAMPM is not None and self.episodeAMPM.lower() == 'pm':
            log('setValues', 'episode contains PM - adding 12 hours to episode hour %s', self.episodeHour)
            self.episodeHour = self.episodeHour + 12
            log('setValues', 'new hour value = %s', self.episodeHour)
        
        # calculate the episode day of year - will be used to create the episode number
        dayOfYear = str(self.episodeReleaseDate.timetuple().tm_yday)
        # build time suffix from the hour, minute, and second values
        timeAsString = format(self.episodeHour, '02') + format(self.episodeMinute, '02') + format(self.episodeSecond, '02')
        self.episodeNumber = int(dayOfYear + str(timeAsString))
        log('setValues', 'day of year %s, time %s = episode number %s', dayOfYear, timeAsString, self.episodeNumber)
        
class SeriesEpisodeMediaParser(BaseMediaParser):
    
    def getSupportedRegexes(self):
        return [
                # \Show Title - s2012e09 - Episode Title.mp4
                r'[\\/](?P<showTitle>[^\\/]+?)[ ]*[-\.]{0,1}[ ]*[sc](?P<seasonNumber>[0-9]+)[e](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
                # \Show Title\01 - Season Title\Show Title - s2012e09 - Episode Title.mp4
                # \Show Title\01\Show Title - s2012e09 - Episode Title.mp4
                r'[\\/](?P<showTitle>[^\\/]+)[\\/][sc|season|chapter|lesson]*?[ ]*?(?P<seasonNumber>[0-9]+)([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[\\/][^\\/]*?[e](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
                # \01 - Season Title\Show Title\Show Title - s2012e09 - Episode Title.mp4
                # \01\Show Title\Show Title - s2012e09 - Episode Title.mp4
                r'[\\/][sc|season|chapter|lesson]*?[ ]*?(?P<seasonNumber>[0-9]+)([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[\\/](?P<showTitle>[^\\/]+)[\\/][^\\/]*?[e](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
                # \Show Title\01 - Season Title\09 - Episode Title.mp4 
                # \Show Title\01\09 - Episode Title.mp4
                # \Training Title\Lesson1\05 - Title.mp4
                r'[\\/](?P<showTitle>[^\\/]+)[\\/][sc|season|chapter|lesson]*?[ ]*?(?P<seasonNumber>[0-9]+)([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[\\/](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
                # \01 - Season Title\Show Title\09 - Episode Title.mp4 
                # \01\Show Title\09 - Episode Title.mp4
                r'[\\/][sc|season|chapter|lesson]*?[ ]*?(?P<seasonNumber>[0-9]+)([-\. ]+(?P<seasonTitle>[^\\/]+)){0,1}[\\/](?P<showTitle>[^\\/]+)[\\/](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
                # \Show Title\2012\e09 - Episode Title.mp4 
                r'[\\/](?P<showTitle>[^\\/]+)[\\/][sc|season|chapter|lesson]*?[ ]*?(?P<seasonNumber>[0-9]+)[\\/][^\\/]*?[e](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
                # \2012\Show Title\e09 - Episode Title.mp4 
                r'[\\/][sc|season|chapter|lesson]*?[ ]*?(?P<seasonNumber>[0-9]+)[\\/](?P<showTitle>[^\\/]+)[\\/][^\\/]*?[e](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
                # \Show Title\2012\09 - Episode Title.mp4 
                r'[\\/](?P<showTitle>[^\\/]+)[\\/][sc|season|chapter|lesson]*?[ ]*?(?P<seasonNumber>[0-9]+)[\\/](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
                # \2012\Show Title\09 - Episode Title.mp4 
                r'[\\/][sc|season|chapter|lesson]*?[ ]*?(?P<seasonNumber>[0-9]+)[\\/](?P<showTitle>[^\\/]+)[\\/](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$' 
            ] 
    
    def setValues(self, match):
        # set the common values
        BaseMediaParser.setValues(self, match)

        # set the season and episode numbers
        self.seasonNumber = int(match.group('seasonNumber').strip())
        self.episodeNumber = int(match.group('episodeNumber').strip())

class SeriesDatedEpisodeMediaParser(BaseDatedSeriesMediaParser):
    
    def __init__(self):
        BaseDatedSeriesMediaParser.__init__(self)
    
    def getSupportedRegexes(self):
        return [
            # \Show Title - s2012e09 - 2015-12-31 - Episode Title.mp4
            r'[\\/](?P<showTitle>[^\\/]+?)[ ]*[-\.]{0,1}[ ]*[sc](?P<seasonNumber>[0-9]+)[e](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeYear>[1-2][0-9][0-9][0-9])[-\. ]{0,1}(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
            # \Show Title - s2012e09 - 12-31-2015 - Episode Title.mp4
            r'[\\/](?P<showTitle>[^\\/]+?)[ ]*[-\.]{0,1}[ ]*[sc](?P<seasonNumber>[0-9]+)[e](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. ]{0,1}(?P<episodeYear>[1-2][0-9][0-9][0-9])[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
            # \Show Title\s2012e09 - 2015-12-31 - Episode Title.mp4
            r'[\\/](?P<showTitle>[^\\/]+)[\\/][sc](?P<seasonNumber>[0-9]+)[e](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeYear>[1-2][0-9][0-9][0-9])[-\. ]{0,1}(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
            # \Show Title\s2012e09 - 12-31-2015 - Episode Title.mp4
            r'[\\/](?P<showTitle>[^\\/]+)[\\/][sc](?P<seasonNumber>[0-9]+)[e](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. ]{0,1}(?P<episodeYear>[1-2][0-9][0-9][0-9])[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
            # \Show Title\s2015\e09 - 2015-12-31 - Episode Title.mp4
            r'[\\/](?P<showTitle>[^\\/]+)[\\/][sc|season|chapter|lesson]*?[ ]*?(?P<seasonNumber>[0-9]+)[\\/][e](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeYear>[1-2][0-9][0-9][0-9])[-\. ]{0,1}(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
            # \Show Title\s2015\e09 - 12-31-2015 - Episode Title.mp4
            r'[\\/](?P<showTitle>[^\\/]+)[\\/][sc|season|chapter|lesson]*?[ ]*?(?P<seasonNumber>[0-9]+)[\\/][e](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. ]{0,1}(?P<episodeYear>[1-2][0-9][0-9][0-9])[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
            # \Show Title\e09 - 2015-12-31 - Episode Title.mp4
            r'[\\/](?P<showTitle>[^\\/]+)[\\/][e](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeYear>[1-2][0-9][0-9][0-9])[-\. ]{0,1}(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
            # \Show Title\e09 - 12-31-2015 - Episode Title.mp4
            r'[\\/](?P<showTitle>[^\\/]+)[\\/][e](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. ]{0,1}(?P<episodeYear>[1-2][0-9][0-9][0-9])[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
            # \Show Title - e09 - 2015-12-31 - Episode Title.mp4
            r'[\\/](?P<showTitle>[^\\/]+?)[ ]*[-\.]{0,1}[ ]*[e](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeYear>[1-2][0-9][0-9][0-9])[-\. ]{0,1}(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$',
            # \Show Title - e09 - 12-31-2015 - Episode Title.mp4
            r'[\\/](?P<showTitle>[^\\/]+?)[ ]*[-\.]{0,1}[ ]*[e](?P<episodeNumber>[0-9]+)[ ]*[-\.]{0,1}[ ]*(?P<episodeMonth>0[1-9]|1[0-2])[-\. ]{0,1}(?P<episodeDay>0[1-9]|1[0-9]|2[0-9]|3[0-1])[-\. ]{0,1}(?P<episodeYear>[1-2][0-9][0-9][0-9])[ ]*[-\.]{0,1}[ ]*(?P<episodeTitle>.*)\.(?P<ext>.+)$'
        ]
        
    def setValues(self, match):
        # set the common values
        BaseDatedSeriesMediaParser.setValues(self, match)

        # get the episode number
        self.episodeNumber = int(match.group('episodeNumber').strip())
        
class CustomMediaParser(BaseMediaParser):

    def __init__(self, config):
        self.parserConfig = config
    
    def getSupportedRegexes(self):
        regexes = []
        
        # Check the config to see if a regex has been set
        configRegex = self.parserConfig.fileNameRegex()
        if configRegex is not None:
            regexes.append(configRegex)
        log('CustomMediaParser.getSupportedRegexes', 'custom file name regexes in use %s', str(regexes))
        return regexes
    
    def setValues(self, match):
        # Set all of the supported values
        self.showTitle = self.scrub(match.group('showTitle').strip())
        # get the season related values
        self.seasonTitle = match.group('seasonTitle').strip()
        self.seasonNumber = int(match.group('seasonNumber').strip())
        # get the episode related values
        self.episodeYear = int(match.group('episodeYear').strip())
        self.episodeMonth = int(match.group('episodeMonth').strip())
        self.episodeDay = int(match.group('episodeDay').strip())
        self.episodeNumber = int(match.group('episodeNumber').strip())
        self.episodeTitle = self.scrub(self.stripPart(match.group('episodeTitle').strip()))
        
        # create the episode release date
        self.episodeReleaseDate = None
        if self.episodeYear is not None and self.episodeMonth is not None and self.episodeDay is not None:
            # Create the date
            self.episodeReleaseDate = datetime.datetime(int(self.episodeYear), int(self.episodeMonth), int(self.episodeDay))

        # create the season number from the episode year
        if self.seasonNumber is None:
            self.seasonNumber = self.episodeYear

# Look for episodes.
def Scan(path, files, mediaList, subdirs, language=None, root=None):

    # List of series parsers
    series_parsers = [SeriesDatedEpisodeMediaParser(), SeriesDateTimeBasedMediaParser(), SeriesDateBasedMediaParser(), SeriesEpisodeMediaParser()]
    # Stores the configuration map
    config_map = ConfigMap()
    
    log('Scan', 'path: %s', path)
    log('Scan', 'files: %s', files)
    log('Scan', 'mediaList: %s', mediaList)
    log('Scan', 'subdirs: %s', subdirs)
    log('Scan', 'language: %s', language)
    log('Scan', 'root: %s', root)
    
    # Scan for video files.
    VideoFiles.Scan(path, files, mediaList, subdirs, root)
    
    for idx, file in enumerate(files):
        log('Scan', 'file: %s', file)
        
        absFilePath = os.path.abspath(file)
        absRootDir = os.path.abspath(root)
        log('Scan', 'absolute file path: %s', absFilePath)
        
        parsers = []
        
        # Check the customParser map for this file
        customParser = config_map.findCustomParser(absRootDir, absFilePath)
        if customParser is not None:
            # If we have a custom parser use only this parser on the file
            parsers = [customParser]
        else:
            # We are using the default parsers
            parsers = series_parsers
            
        # Iterate over the list of parsers and parse the file path
        for parser in parsers:
            log('Scan', 'parser %s', parser)
            if parser.containsMatch(absFilePath) is True:
                log('Scan', 'parser %s contains match - parsing file path', parser)
                parser.parse(absFilePath, language)

                showTitle = parser.getShowTitle()
                log('Scan', 'show title: %s', showTitle)
                seasonNumber = parser.getSeasonNumber()
                log('Scan', 'season number: %s', seasonNumber)
                seasonYear = parser.getSeasonYear()
                log('Scan', 'season year: %s', seasonYear)
                episodeNumber = parser.getEpisodeNumber()
                log('Scan', 'episode number: %s', episodeNumber)
                episodeTitle = parser.getEpisodeTitle()
                log('Scan', 'episode title: %s', episodeTitle)
        
                vid = Media.Episode(showTitle, seasonNumber, episodeNumber, episodeTitle, seasonYear)
                vid.parts.append(file)
                mediaList.append(vid)
                break
            
    # stack files
    log('Scan', 'stack media')
    Stack.Scan(path, files, mediaList, subdirs)
    log('Scan', 'media list %s', mediaList)
