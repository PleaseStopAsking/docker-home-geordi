# Version Date: 2021-07-03

import datetime, os, sys, time, re, locale, ConfigParser, urllib2, urllib
from string import Template
from xml.dom import minidom

# Series agent name
SERIES_AGENT_NAME = 'Extended Personal Media Shows'

def logDebug(methodName, message, *args):
    if bool(Prefs['logger.debug.enabled']):
        Log(methodName + ' :: ' + message, *args)

def log(methodName, message, *args):
    Log(methodName + ' :: ' + message, *args)

def isBlank (string):
    '''
    Tests whether the string is blank
    '''
    return not(string and string.strip())

def isNotBlank (string):
    '''
    Tests whether the string is not blank
    '''
    return bool(string and string.strip())

def convertToList(string, delimiter=','):
    '''
    Converts the comma separated string into a list

    None is returned if the string is none
    '''
    returnVal = None
    if string is not None:
        returnVal = [x.strip() for x in string.split(delimiter)]
    return returnVal

# Only use unicode if it's supported, which it is on Windows and OS X,
# but not Linux. This allows things to work with non-ASCII characters
# without having to go through a bunch of work to ensure the Linux
# filesystem is UTF-8 "clean".
#
def unicodize(s):
    filename = s

    logDebug('unicodize', 'before unicodizing: %s', str(filename))
    if os.path.supports_unicode_filenames:
        try: filename = unicode(s.decode('utf-8'))
        except: pass
    logDebug('unicodize', 'after unicodizing: %s', str(filename))
    return filename

def findFile(filePaths, fileNames):
    '''
    Find one of the specified file names in the list starting at the lowest directory passed in and
    walking up the directory tree until the root directory is found or one of the files in the list is found
    '''
    for filePath in filePaths:
        rootDirFound = False
        parentDir = filePath

        # Get the parent directory for the file
        if os.path.isfile(filePath):
            parentDir = os.path.dirname(parentDir)

        # iterate over the directory
        while not rootDirFound:
            logDebug('findFile', 'looking in parent directory %s', parentDir)
            # create the file path
            for fileName in fileNames:
                pathToFind = os.path.normpath(os.path.normcase(os.path.join(parentDir, fileName)))
                logDebug('findFile', 'determining whether file %s exists', pathToFind)
                if os.path.exists(pathToFind) and os.path.isfile(pathToFind):
                    logDebug('findFile', 'file %s exists', pathToFind)
                    return pathToFind
                else:
                    logDebug('findFile', 'file %s does not exist', pathToFind)

            # go up a directory
            logDebug('findFile', 'going up a directory')
            newDir = os.path.abspath(os.path.dirname( parentDir ))

            logDebug('findFile', 'new directory path %s', newDir)
            # if the new directory and parent directory are the same then we have reached the top directory - stop looking for the file
            if newDir == parentDir:
                logDebug('findFile', 'root directory %s found - stopping directory traversal', newDir)
                rootDirFound = True
            else:
                parentDir = newDir

    return None

def isSubdir(path, directory):
    '''
    Returns true if *path* in a subdirectory of *directory*.
    '''
    if len(path) > len(directory):
        sep = os.path.sep.encode('ascii') if isinstance(directory, bytes) else os.path.sep
        dirComp = directory.rstrip(sep) + sep
        logDebug('isSubdir','comparing [%s] to [%s]', path, dirComp)
        if path.startswith(dirComp):
            logDebug('isSubdir', 'path is a subdirectory')
            return True
    return False

def loadTextFromFile(filePath):
    '''
    Load the text text from the specified file
    '''
    textUnicode = None
    # If the file exists read in its contents
    if os.path.exists(filePath) is True:
        text = None
        logDebug('loadTextFromFile', 'file exists - reading contents')
        try:
            # Read the text from the file
            text = Core.storage.load(filePath, False)
        except Exception as e:
            logDebug('loadTextFromFile', 'error occurred reading contents of file %s : %s', filePath, e)

        # try to decode the contents
        try:
            # decode using the system default
            logDebug('loadTextFromFile', 'decoding string using utf-8 - not ignoring errors')
            textUnicode = unicode(text, 'utf-8')
        except Exception as e:
            logDebug('loadTextFromFile', 'could not decode contents of summary file %s : %s', filePath, e)
            # decode using utf-8 and ignore errors
            logDebug('loadTextFromFile', 'decoding string using utf-8 - ignoring errors')
            textUnicode = unicode(text, 'utf-8', errors='ignore')

    return textUnicode

def getPlexToken():
    logDebug('getPlexToken', 'getting Plex token from the environment')
    return os.environ['PLEXTOKEN']

def isPlexTokenSet():
    return getPlexToken() is not None and isNotBlank(getPlexToken())
    
def getSummaryFileExtension():
    '''
    Gets the summary file extension to use from the plugin preferences
    '''
    fileExt = Prefs['summary.file.extension']
    if isBlank(fileExt):
        fileExt = 'summary'
    logDebug('getSummaryFileExtension', 'using summary file extension %s', fileExt)
    fileExt = '.'+fileExt
    return fileExt

def getMetadataFileExtension():
    '''
    Gets the metadata file extension to use from the plugin preferences
    '''
    fileExt = Prefs['metadata.file.extension']
    if isBlank(fileExt):
        fileExt = 'metadata'
    logDebug('getMetadataFileExtension', 'using metadata file extension %s', fileExt)
    fileExt = '.'+fileExt
    return fileExt
    
def setSeasonMetadata(seasonDataMap):
    '''
    Calls the web API to set the season title and summary
    '''
    # if the plex toke is not set - skip
    if(not isPlexTokenSet()):
        log('setSeasonMetadata', 'Plex token is not set - skipping season title and summary update')
        return
    
    log('setSeasonMetadata', 'Plex token is set - updating season title and summary update')
    plexToken = getPlexToken()
    #Get the library section id from the XML metadata
    metadataCheckUrl = 'http://127.0.0.1:32400/library/metadata/'+str(seasonDataMap['id'])+'?checkFiles=1&includeExtras=1&X-Plex-Token=' + plexToken
    debugMetadataCheckUrl = 'http://127.0.0.1:32400/library/metadata/'+str(seasonDataMap['id'])+'?checkFiles=1&includeExtras=1'
    logDebug('setSeasonMetadata','url: %s', debugMetadataCheckUrl)

    metadataXml = urllib2.urlopen(metadataCheckUrl) 
    xmldoc = minidom.parse(metadataXml)
    mediaContainer = xmldoc.getElementsByTagName('MediaContainer')[0]
    librarySectionId = mediaContainer.attributes['librarySectionID'].value
    logDebug('setSeasonMetadata','librarySectionId: %s', str(librarySectionId))

    # Call the web API to set the season title and summary
    data = {'type':'3','id':seasonDataMap['id'],'title.value':seasonDataMap['title'],'summary.value':seasonDataMap['summary'],'summary.locked':'0','X-Plex-Token':plexToken}
    dataEncoded = urllib.urlencode(data)
    updateSeasonUrl = 'http://127.0.0.1:32400/library/sections/'+str(librarySectionId)+'/all?' + dataEncoded
    # log the request that was made
    debugData = {'type':'3','id':seasonDataMap['id'],'title.value':seasonDataMap['title'],'summary.value':seasonDataMap['summary'],'summary.locked':'0'}
    debugDataEncoded = urllib.urlencode(debugData)
    debugUpdateSeasonUrl = 'http://127.0.0.1:32400/library/sections/'+str(librarySectionId)+'/all?' + debugDataEncoded
    logDebug('setSeasonMetadata','url: %s', debugUpdateSeasonUrl)
    
    opener = urllib2.build_opener(urllib2.HTTPHandler)
    request = urllib2.Request(updateSeasonUrl,data=urllib.urlencode({'dummy':'dummy'}))
    request.add_header('Content-Type', 'text/html')
    request.get_method = lambda: 'PUT'
    opener.open(request)
    logDebug('setSeasonMetadata', 'season updated')

class BaseMediaParser(object):
    '''
        Parses the file name and determines the type of tilethat was found
    '''

    fileNameRegex = r'^(?P<fileWithoutExt>.*)\..+$'

    # Episode name REGEX
    partRegexes = [
                    r'(?P<episodeTitle>.+)(\.[ ]*|-[ ]*)(part[0-9]+|pt[0-9]+)',
                    r'(?P<episodeTitle>.+)([ ]+)(part[0-9]+|pt[0-9]+)'
                    ]

    def __init__(self):
        self.showTitle = None
        self.seasonNumber = None
        self.seasonTitle = None
        self.episodeTitle = None
        self.formattedEpisodeTitle = None
        self.episodeSummary = None
        self.episodeReleaseDate = None
        self.episodeWriters = None
        self.episodeDirectors = None
        self.metadataExists = False

    def stripPart(self, episodeTitle):
        processed = episodeTitle
        # Test whether it contains part
        for partRegex in self.partRegexes:
            match = re.search(partRegex, processed)
            if match:
                logDebug('stripPart', 'episode title %s contains part', processed)
                processed = match.group('episodeTitle').strip()
                logDebug('stripPart', 'stripped episode title: %s', processed)
                break

        return processed
       
    def scrub(self, string, charsToRemove):
        processed = string
        stringAsList = list(charsToRemove)
        i = 0
        while i + 3 <= len(stringAsList):
            processed = re.sub(re.escape(stringAsList[i]), stringAsList[i+2], processed)
            i = i + 4
        if i < len(stringAsList):
            logDebug('scrubString', 'did not process the remaining characters [%s] in the string - verify the scrub string is formatted correctly i.e. A=B,C=D', charsToRemove[i:len(charsToRemove)])
        logDebug('scrubString', 'original: [%s] scrubbed: [%s]', string, processed)
        return processed

    def setValues(self, match):
        # set the show title
        if 'showTitle' in match.groupdict() and match.group('showTitle') is not None:
            self.showTitle = self.stripPart(match.group('showTitle').strip())
            logDebug('setValues', 'show title: %s', str(self.showTitle))

        # set the season number
        self.seasonNumber = None
        if 'seasonNumber' in match.groupdict() and match.group('seasonNumber') is not None:
            self.seasonNumber = match.group('seasonNumber').strip()
            logDebug('setValues', 'season number: %s', str(self.seasonNumber))

        # set the season title
        if 'seasonTitle' in match.groupdict() and match.group('seasonTitle') is not None:
            self.seasonTitle = self.stripPart(match.group('seasonTitle').strip())
            logDebug('setValues', 'season title: %s', str(self.seasonTitle))
               
        # get the file name without the extension
        fileNameMatch = re.search(self.fileNameRegex, self.mediaFile)
        fileWithoutExt = None
        if fileNameMatch:
            fileWithoutExt = fileNameMatch.group('fileWithoutExt').strip()
            logDebug('setValues', 'file name without extension %s', fileWithoutExt)

        # retrieve values from the metadata file (if it exists)
        if bool(Prefs['use.episode.metadata.enabled']):
            metadataFilePath = fileWithoutExt + getMetadataFileExtension()
            logDebug('setValues', 'looking for metadata file %s', metadataFilePath)
            if os.path.exists(metadataFilePath):
                logDebug('setValues', 'episode metadata file %s exists', metadataFilePath)
                self.metadataExists = True
                fileMetadata = EpisodeMetadataFile(metadataFilePath)
                release = fileMetadata.release()
                if isNotBlank(release):
                    self.episodeReleaseDate = datetime.datetime.strptime(release, '%Y-%m-%d')
                    log('setValues', 'episode.metadata - release: %s', release)
                title = fileMetadata.title()
                if title is not None:
                    self.episodeTitle = title
                    log('setValues', 'episode.metadata - title: %s', title)
                summary = fileMetadata.summary()
                if summary is not None:
                    self.episodeSummary = summary
                    log('setValues', 'episode.metadata - summary: %s', summary)
                writers = fileMetadata.writers()
                if writers is not None:
                    self.episodeWriters = writers
                    log('setValues', 'episode.metadata - writers: %s', writers)
                directors = fileMetadata.directors()
                if directors is not None:
                    self.episodeDirectors = directors
                    log('setValues', 'episode.metadata - directors: %s', directors)
            else:
                logDebug('setValues', 'episode metadata file does not exist')

        # If not using metadata file, parse values from the file name
        if not self.metadataExists:
            log('setValues', "setting episode metadata from file name")
            # set the episode title
            self.episodeTitle = self.stripPart(match.group('episodeTitle').strip())
            # check to see if title should be scrubbed
            if bool(Prefs['episode.title.scrub.enabled']):
                episodeScrubChars = Prefs['episode.title.scrub.characters']
                if isNotBlank(episodeScrubChars):
                    logDebug('setValues', 'scrubbing enabled - using scrub characters [%s] ', episodeScrubChars)
                    self.episodeTitle = self.scrub(self.episodeTitle, episodeScrubChars)
                else:
                    logDebug('setValues', 'scrubbing enabled - scrub characters are blank [%s] - skipping scrubbing', episodeScrubChars)

        # If the summary file exists, set the episode summary from the summary file
        summaryFilePath = fileWithoutExt + getSummaryFileExtension()
        logDebug('setValues', 'looking for summary file %s', summaryFilePath)
        # If the summary file exists read in the contents
        if os.path.exists(summaryFilePath) is True:
            logDebug('setValues', 'episode summary file %s exists', summaryFilePath)
            self.episodeSummary = loadTextFromFile(summaryFilePath)
        else:
            logDebug('setValues', 'episode summary file does not exist')

        # set the formatted episode title
        self.formattedEpisodeTitle = self.episodeTitle

    def getSupportedRegexes(self):
        return []

    def postSetValues(self):
        pass

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


    def parse(self, mediaFile):
        self.mediaFile = mediaFile

        # Iterate over the list of regular expressions
        for regex in self.getSupportedRegexes():
            # Find out what file format is being used
            match = re.search(regex, mediaFile, re.IGNORECASE)
            logDebug('parse', 'regex %s - matches: %s', regex, match)
            if match:
                logDebug('parse', 'found matches')
                self.setValues(match)
                break

    def getSeasonNumber(self):
        return self.seasonNumber

    def getSeasonTitle(self):
        return self.seasonTitle

    def getShowTitle(self):
        return self.showTitle

    def getEpisodeTitle(self):
        return self.episodeTitle

    def getFormattedEpisodeTitle(self):
        return self.formattedEpisodeTitle

    def getEpisodeSummary(self):
        return self.episodeSummary

    def getEpisodeReleaseDate(self):
        return self.episodeReleaseDate

    def getEpisodeWriters(self):
        return self.episodeWriters

    def getEpisodeDirectors(self):
        return self.episodeDirectors
        
class BaseDatedSeriesMediaParser(BaseMediaParser):

    def __init__(self):
        BaseMediaParser.__init__(self)
        self.episodeYear = None
        self.episodeMonth = None
        self.episodeDay = None

    def setValues(self, match):
        # set the common values
        BaseMediaParser.setValues(self, match)

        # set the episode release date
        # if episodeMonth and episodeDay is present in the regex then the episode release date is in the file name and will be used
        if 'episodeMonth' in match.groupdict() and 'episodeDay' in match.groupdict():
            logDebug('setValues', 'episodeMonth found in the regular expression - extracting release date from the file name')
            self.episodeYear = None
            if 'episodeYear' in match.groupdict():
                self.episodeYear = int(match.group('episodeYear').strip())
            # if the regex did not contain a season number but contains an episode year - use the episode year
            if self.seasonNumber is None and self.episodeYear is not None:
                self.seasonNumber = str(self.episodeYear)
            # if the regex did not contain a year use the season number
            if self.episodeYear is None and self.seasonNumber is not None and int(self.seasonNumber) >= 1000:
                self.episodeYear = int(self.seasonNumber)
            self.episodeMonth = int(match.group('episodeMonth').strip())
            self.episodeDay = int(match.group('episodeDay').strip())
            # Create the date
            logDebug('setValues', 'year %s month %s day %s', self.episodeYear, self.episodeMonth, self.episodeDay)

        if not self.metadataExists:
            self.episodeReleaseDate = datetime.datetime(self.episodeYear, self.episodeMonth, self.episodeDay)
            logDebug('setValues', 'episode date: %s', str(self.episodeReleaseDate))

            # check to see if the "Add date to episode title" preference is enabled
            if bool(Prefs['episode.add.date.to.title.enabled']):
                # prepend the date to the title
                self.formattedEpisodeTitle = self.formatEpisodeReleaseDate() + ' ' + self.episodeTitle
                logDebug('setValues', "formatted episode title: %s", self.formattedEpisodeTitle)

    def formatEpisodeReleaseDate(self):
        episodeDateFormatType = Prefs['episode.add.date.to.title.format']            
        logDebug('formatEpisodeReleaseDate', "Add date to episode title format = %s", episodeDateFormatType)
        
        episodeDate = datetime.date(self.episodeYear, self.episodeMonth, self.episodeDay)
        # pick the correct format type based on what was selected
        formattedDateString = None
        if episodeDateFormatType == 'YYYY-MM-DD':
            log('formatEpisodeReleaseDate', 'formatting using YYYY-MM-DD')
            formattedDateString = episodeDate.strftime('%Y-%m-%d')
        elif episodeDateFormatType == 'YYYY/MM/DD':
            log('formatEpisodeReleaseDate', 'formatting using YYYY/MM/DD')
            formattedDateString = episodeDate.strftime('%Y/%m/%d')
        elif episodeDateFormatType == 'MM-DD':
            log('formatEpisodeReleaseDate', 'formatting using MM-DD')
            formattedDateString = episodeDate.strftime('%m-%d')
        elif episodeDateFormatType == 'MM/DD':
            log('formatEpisodeReleaseDate', 'formatting using MM/DD')
            formattedDateString = episodeDate.strftime('%m/%d')
        log('formatEpisodeReleaseDate', 'formatted date %s', formattedDateString)
        return formattedDateString

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
        # if the regex contains PM then add 12 hours to episode
        if self.episodeAMPM is not None and self.episodeAMPM.lower() == 'pm':
            log('setValues', 'episode contains PM - adding 12 hours to episode hour %s', self.episodeHour)
            self.episodeHour = self.episodeHour + 12
            log('setValues', 'new value = %s', self.episodeHour)            
        self.episodeMinute = int(match.group('episodeMinute').strip())
        self.episodeSecond = int(match.group('episodeSecond').strip())
        log('setValues', 'parsed time: hour %s minute %s second %s', self.episodeHour, self.episodeMinute, self.episodeSecond)

        if not self.metadataExists:
            # check to see if the "Add time to episode title" preference is enabled
            if (bool(Prefs['episode.add.time.to.title.enabled']) and bool(Prefs['episode.add.date.to.title.enabled'])):
                # prepend the time to the title
                self.formattedEpisodeTitle = self.formatEpisodeReleaseDate() + ' ' + self.formatEpisodeReleaseTime() + ' ' + self.episodeTitle
            # check to see if the "Add date to episode title" preference is enabled
            elif bool(Prefs['episode.add.time.to.title.enabled']):
                # prepend the date to the title
                self.formattedEpisodeTitle = self.formatEpisodeReleaseTime() + ' ' + self.episodeTitle
            # check to see if the "Add date to episode title" preference is enabled
            elif bool(Prefs['episode.add.date.to.title.enabled']):
                # prepend the date to the title
                self.formattedEpisodeTitle = self.formatEpisodeReleaseDate() + ' ' + self.episodeTitle
            logDebug('setValues', "formatted episode title: %s", self.formattedEpisodeTitle)
 
    def formatEpisodeReleaseTime(self):
        # format the episode release time
        episodeTimeFormatType = Prefs['episode.add.time.to.title.format']            
        logDebug('setValues', "Add time to episode title format = %s", episodeTimeFormatType)

        # format the time parts using the user configured setting
        episodeTime = datetime.time(self.episodeHour, self.episodeMinute, self.episodeSecond)
        # if the format type is 24 hours and regex contains AM/PM then calculate new hour value
        formattedTimeString = None
        if episodeTimeFormatType == '24 Hour':
            log('formatEpisodeReleaseTime', 'formatting using 24 hour time')
            formattedTimeString = episodeTime.strftime('%H:%M:%S')
        elif episodeTimeFormatType == 'AM/PM':
            log('formatEpisodeReleaseTime', 'formatting using AM/PM time')
            formattedTimeString = episodeTime.strftime('%I:%M:%S %p')
        log('formatEpisodeReleaseTime', 'formatted time %s', formattedTimeString)
        return formattedTimeString
                
class SeriesEpisodeMediaParser(BaseMediaParser):

    def __init__(self):
        BaseMediaParser.__init__(self)

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
        
        if not self.metadataExists:
            # check to see if the "use last modified timestamp" preference is enabled
            if bool(Prefs['episode.use.last.modified.timestamp.enabled']):
                logDebug('setValues', "Use last modified timestamp option is enabled - extracting release date from the file's last modified timestamp")
                # Get the release date from the file
                self.episodeReleaseDate = datetime.date.fromtimestamp(os.path.getmtime(self.mediaFile))
                logDebug('setValues', 'episode date: %s', str(self.episodeReleaseDate))
            # check to see if the "use last modified timestamp" preference is enabled
            elif bool(Prefs['episode.use.created.timestamp.enabled']):
                logDebug('setValues', "Use created timestamp option is enabled - extracting release date from the file's created timestamp")
                # Get the release date from the file
                self.episodeReleaseDate = datetime.date.fromtimestamp(os.path.getctime(self.mediaFile))
                logDebug('setValues', 'episode date: %s', str(self.episodeReleaseDate))
        

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
        
def Start():
    log('Start', 'starting agents %s, %s', SERIES_AGENT_NAME)
    pass

class ShowMetadataFile(object):
    '''
        Gets the show metadata from the specified file. 
        File must follow https://docs.python.org/2/library/configparser.html# pattern
    '''

    # constants
    SECTION_METADATA = 'metadata'
                        
    def __init__(self, filePath):
        self.filePath = filePath
        defaults = {
          'title' : None,
          'summary' : None,
          'release' : None,
          'studio' : None,
          'genres' : None,
          'collections' : None,
          'actors' : None
        }
        self.metadata = ConfigParser.RawConfigParser(defaults)
        self.metadata.read(filePath)

    def title(self):
        return self.metadata.get(self.SECTION_METADATA, 'title')

    def summary(self):
        return self.metadata.get(self.SECTION_METADATA, 'summary')

    def release(self):
        return self.metadata.get(self.SECTION_METADATA, 'release')

    def studio(self):
        return self.metadata.get(self.SECTION_METADATA, 'studio')

    def genres(self):
        return convertToList(self.metadata.get(self.SECTION_METADATA, 'genres'))

    def collections(self):
        return convertToList(self.metadata.get(self.SECTION_METADATA, 'collections'))

    def actors(self):
        return convertToList(self.metadata.get(self.SECTION_METADATA, 'actors'))

class SeasonMetadataFile(object):
    '''
        Gets the season metadata from the specified file. 
        File must follow https://docs.python.org/2/library/configparser.html# pattern
    '''

    # constants
    SECTION_METADATA = 'metadata'
                        
    def __init__(self, filePath):
        self.filePath = filePath
        defaults = {
          'title' : None,
          'summary' : None
        }
        self.metadata = ConfigParser.RawConfigParser(defaults)
        self.metadata.read(filePath)

    def title(self):
        return self.metadata.get(self.SECTION_METADATA, 'title')

    def summary(self):
        return self.metadata.get(self.SECTION_METADATA, 'summary')


class EpisodeMetadataFile(object):
    '''
        Gets the episode metadata from the specified file. 
        File must follow https://docs.python.org/2/library/configparser.html# pattern
    '''

    # constants
    SECTION_METADATA = 'metadata'

    def __init__(self, filePath):
        self.filePath = filePath
        defaults = {
          'title' : None,
          'summary' : None,
          'release' : None,
          'writers' : None,
          'directors' : None
        }
        self.metadata = ConfigParser.RawConfigParser(defaults)
        self.metadata.read(filePath)

    def title(self):
        return self.metadata.get(self.SECTION_METADATA, 'title')

    def summary(self):
        return self.metadata.get(self.SECTION_METADATA, 'summary')

    def release(self):
        return self.metadata.get(self.SECTION_METADATA, 'release')

    def writers(self):
        return convertToList(self.metadata.get(self.SECTION_METADATA, 'writers'))

    def directors(self):
        return convertToList(self.metadata.get(self.SECTION_METADATA, 'directors'))

class ExtendedPersonalMediaAgentTVShows(Agent.TV_Shows):
    name = SERIES_AGENT_NAME
    languages = Locale.Language.All()
    accepts_from = ['com.plexapp.agents.localmedia']

    def search(self, results, media, lang):
        logDebug('search', 'media id: %s', media.id)
        logDebug('search', 'media file name: %s', str(media.filename))
        logDebug('search', 'media primary metadata: %s', str(media.primary_metadata))
        logDebug('search', 'media primary agent: %s', str(media.primary_agent))
        logDebug('search', 'media title: %s', str(media.title))
        logDebug('search', 'media show: %s', str(media.show))
        logDebug('search', 'media name: %s', str(media.name))
        logDebug('search', 'media season: %s', str(media.season))
        logDebug('search', 'media episode: %s', str(media.episode))

        # Compute the GUID based on the media hash.
        try:
            part = media.items[0].parts[0]
            # Get the modification time to use as the year.
            filename = unicodize(part.file)
            log('search', 'part file name: %s', filename)
        except:
            log('search', 'part does not exist')

        results.Append(MetadataSearchResult(id=media.id, name=media.show, year=None, lang=lang, score=100))

    def update(self, metadata, media, lang):
        #test.test('Extended Personal Media - Scan')
        logDebug('update', 'meta data agent object id: %s', id(self))
        logDebug('update', 'metadata: %s', str(metadata))
        logDebug('update', 'media: %s', str(media))
        logDebug('update', 'lang: %s', str(lang))
        logDebug('update', 'show id: %s', media.id)
        logDebug('update', 'show title: %s', media.title)
        # list of file paths
        showFilePaths = []

        # store the show title from one of the episodes
        showTitle = None
        for s in media.seasons:
            logDebug('update', 'season %s', s)
            seasonId = media.seasons[s].id
            seasonMetadata = metadata.seasons[s]
            logDebug('update', 'season id: %s', seasonId)
            logDebug('update', 'season metadata %s', seasonMetadata)
            logDebug('update', 'season title: %s', seasonMetadata.title)
            metadata.seasons[s].index = int(s)
            seasonFilePaths = []

            # store the season number/title from one of the episodes
            seasonTitle = None   
            seasonNumber = None
            for e in media.seasons[s].episodes:
                logDebug('update', 'episode: %s', e)
                # Make sure metadata exists, and find sidecar media.
                episodeId = media.seasons[s].episodes[e].id
                episodeMetadata = metadata.seasons[s].episodes[e]
                logDebug('update', 'episode id: %s', episodeId)
                logDebug('update', 'episode metadata: %s', episodeMetadata)
                episodeMedia = media.seasons[s].episodes[e].items[0]

                file = episodeMedia.parts[0].file
                logDebug('update', 'episode file path: %s', file)
                absFilePath = os.path.abspath(unicodize(file))
                log('update', 'absolute file path: %s', absFilePath)

                # list of series parsers
                series_parsers = [SeriesDatedEpisodeMediaParser(), SeriesDateTimeBasedMediaParser(), SeriesDateBasedMediaParser(), SeriesEpisodeMediaParser()]
                # Iterate over the list of parsers and parse the file path
                for parser in series_parsers:
                    if parser.containsMatch(absFilePath) is True:
                        logDebug('update', 'parser object id: %s', id(parser))
                        log('update', 'parser %s contains match - parsing file path', parser)
                        parser.parse(absFilePath)

                        # set the episode data
                        episodeMetadata.title = parser.getFormattedEpisodeTitle()
                        log('update', 'episode.title: %s', episodeMetadata.title)
                        episodeMetadata.summary = parser.getEpisodeSummary()
                        log('update', 'episode.summary: %s', episodeMetadata.summary)
                        episodeMetadata.originally_available_at = parser.getEpisodeReleaseDate()
                        log('update', 'episode.originally_available_at: %s', episodeMetadata.originally_available_at)
                        writers = parser.getEpisodeWriters()
                        episodeMetadata.writers.clear()
                        if writers is not None:
                            log('update', 'episode.writers: %s', str(writers))
                            for writer in writers:
                                metadataWriter = episodeMetadata.writers.new()
                                metadataWriter.name = writer
                        directors = parser.getEpisodeDirectors()
                        episodeMetadata.directors.clear()
                        if directors is not None:
                            log('update', 'episode.directors: %s', str(directors))
                            for director in directors:
                                metadataDirector = episodeMetadata.directors.new()
                                metadataDirector.name = director

                        # add the file path to the season file path list
                        seasonFilePaths = self.addFilePath(seasonFilePaths, absFilePath)
                        # add the file path to the show file path list
                        showFilePaths = self.addFilePath(showFilePaths, absFilePath)

                        # get the show title from one of the episodes
                        if showTitle is None and isNotBlank(parser.getShowTitle()):
                            showTitle = parser.getShowTitle()

                        # get the season title from one of the episodes
                        if seasonTitle is None and isNotBlank(parser.getSeasonTitle()):
                            seasonTitle = parser.getSeasonTitle()

                        # get the season number from one of the episodes
                        if seasonNumber is None and isNotBlank(parser.getSeasonNumber()):
                            seasonNumber = parser.getSeasonNumber()

                        break

            logDebug('update', 's = %s, season number = %s', s, seasonNumber)
            seasonSummary = None
            if bool(Prefs['use.season.metadata.enabled']):
                logDebug('update', 'use season metadata file option is enabled - looking for metadata file')
                metadataFileExt = getMetadataFileExtension()
                seasonMetadataFileNames = [showTitle + '-S' + seasonNumber + metadataFileExt, 
                                showTitle + '-s' + seasonNumber + metadataFileExt, 
                                showTitle + '-C' + seasonNumber + metadataFileExt, 
                                showTitle + '-c' + seasonNumber + metadataFileExt, 
                                showTitle + '-L' + seasonNumber + metadataFileExt, 
                                showTitle + '-l' + seasonNumber + metadataFileExt, 
                                'season-' + seasonNumber + metadataFileExt, 
                                'chapter-' + seasonNumber + metadataFileExt, 
                                'lesson-' + seasonNumber + metadataFileExt, 
                                'S' + seasonNumber + metadataFileExt, 
                                's' + seasonNumber + metadataFileExt, 
                                'C' + seasonNumber + metadataFileExt, 
                                'c' + seasonNumber + metadataFileExt, 
                                'L' + seasonNumber + metadataFileExt, 
                                'l' + seasonNumber + metadataFileExt]
                
                logDebug('update', 'looking for files with names %s in path list %s', str(seasonMetadataFileNames), str(seasonFilePaths))
                seasonMetadataFilePath = findFile(seasonFilePaths, seasonMetadataFileNames)
                if seasonMetadataFilePath is not None:
                    log('update', 'found season metadata file at %s', seasonMetadataFilePath)
                    fileMetadata = SeasonMetadataFile(seasonMetadataFilePath)
                    if fileMetadata.title() is not None:
                        seasonTitle = fileMetadata.title()
                        log('update', 'season.title: %s', seasonTitle)
                    if fileMetadata.summary() is not None:
                        seasonSummary = fileMetadata.summary()
                        log('update', 'season.summary: %s', seasonSummary)
                else:
                    logDebug('update', 'season metadata file not found')
            
            # Check for season summary
            summaryFileExt = getSummaryFileExtension()
            # Build the list of the file names that we should look for
            seasonSummaryFileNames = [showTitle + '-S' + seasonNumber + summaryFileExt, 
                                showTitle + '-s' + seasonNumber + summaryFileExt, 
                                showTitle + '-C' + seasonNumber + summaryFileExt, 
                                showTitle + '-c' + seasonNumber + summaryFileExt, 
                                showTitle + '-L' + seasonNumber + summaryFileExt, 
                                showTitle + '-l' + seasonNumber + summaryFileExt, 
                                'season-' + seasonNumber + summaryFileExt, 
                                'chapter-' + seasonNumber + summaryFileExt, 
                                'lesson-' + seasonNumber + summaryFileExt, 
                                'S' + seasonNumber + summaryFileExt, 
                                's' + seasonNumber + summaryFileExt, 
                                'C' + seasonNumber + summaryFileExt, 
                                'c' + seasonNumber + summaryFileExt, 
                                'L' + seasonNumber + summaryFileExt, 
                                'l' + seasonNumber + summaryFileExt]
            
            logDebug('update', 'looking for files with names %s in path list %s', str(seasonSummaryFileNames), str(seasonFilePaths))
            seasonSummaryFilePath = findFile(seasonFilePaths, seasonSummaryFileNames)
            if seasonSummaryFilePath is not None:
                log('update', 'found season summary file at %s', seasonSummaryFilePath)
                seasonSummary = loadTextFromFile(seasonSummaryFilePath)
            else:
                logDebug('update', 'season summary file not found')
            
            # create a map for the season data that we want to update
            seasonDataMap = {'id':seasonId, 'title':'', 'summary':''}
            if seasonSummary is not None:
                #seasonMetadata.summary = seasonSummary
                seasonDataMap['summary'] = seasonSummary
                log('update', 'season.summary: %s', seasonSummary)
            
            # Set the season title
            if seasonTitle is not None:
                #seasonMetadata.title = seasonTitle
                seasonDataMap['title'] = seasonTitle
                log('update', 'season.title: %s', seasonTitle)
            # Set the season details
            setSeasonMetadata(seasonDataMap)
            
        showMetadataExists = False
        if bool(Prefs['use.show.metadata.enabled']):
            logDebug('update', 'use metadata file option is enabled - extracting metadata from metadata file')
            metadataFileExt = getMetadataFileExtension()
            showMetadataFilePath = findFile(showFilePaths, [showTitle + metadataFileExt, 'show' + metadataFileExt])
            if showMetadataFilePath is not None:
                logDebug('update', 'found show metadata file at %s', showMetadataFilePath)
                showMetadataExists = True
                fileMetadata = ShowMetadataFile(showMetadataFilePath)
                title = fileMetadata.title()
                if title is not None:
                    metadata.title = title
                    log('update', 'show.title: %s', title)
                summary = fileMetadata.summary()
                if summary is not None:
                    metadata.summary = summary
                    log('update', 'show.summary: %s', summary)
                release = fileMetadata.release()
                if isNotBlank(release):
                    metadata.originally_available_at = datetime.datetime.strptime(release, '%Y-%m-%d')
                    log('update', 'show.release: %s', release)
                studio = fileMetadata.studio()
                if studio is not None:
                    metadata.studio = studio
                    log('update', 'show.studio: %s', studio)
                genres = fileMetadata.genres() 
                metadata.genres.clear()
                if genres is not None:
                    metadata.genres = genres
                    log('update', 'show.genres: %s', genres)
                collections = fileMetadata.collections() 
                metadata.collections.clear()
                if collections is not None:
                    metadata.collections = collections
                    log('update', 'show.collections: %s', collections)
                actors = fileMetadata.actors() 
                metadata.roles.clear()
                if actors is not None:
                    for actor in actors:
                        metadataRole = metadata.roles.new()
                        metadataRole.name = actor
                    log('update', 'show.actors: %s', actors)
            else:
                logDebug('update', 'show metadata file not found')
        
        if not showMetadataExists:
            # set the show title
            if showTitle is not None:
                metadata.title = showTitle
                log('update', 'show.title - title: %s', showTitle)
            
            # clear other values
            log('update', 'clearing show summary, originally available at, studio and genres attributes')
            metadata.summary = None
            metadata.originally_available_at = None
            metadata.studio = None
            metadata.genres = []


        # Check for show summary file (if present, this overrides any summary in metadata file)
        summaryFileExt = getSummaryFileExtension()
        showSummaryFilePath = findFile(showFilePaths, [showTitle + summaryFileExt, 'show' + summaryFileExt])
        if showSummaryFilePath is not None:
            logDebug('update', 'found show summary file at %s', showSummaryFilePath)
            metadata.summary = loadTextFromFile(showSummaryFilePath)
            log('update', 'show.summary: %s', metadata.summary)
        else:
            logDebug('update', 'show summary file not found')

    def addFilePath(self, filePaths, newFilePath):
        '''
        Adds the specified file path to the list if it is a sub-directory or a unique file path
        '''
        evalPaths = []

        newDirPath = newFilePath
        if os.path.isfile(newDirPath):
            newDirPath = os.path.dirname(newDirPath)
        # determine if the new path is a sub-path or a new path
        logDebug('addFilePath', 'verifying file path [%s] should be added', newDirPath)
        appendPath = True
        for path in filePaths:
            path = os.path.normpath(os.path.normcase(path))
            logDebug('addFilePath', 'existing path [%s]', path)
            newDirPath = os.path.normpath(os.path.normcase(newDirPath))
            logDebug('addFilePath', 'new path [%s]', newDirPath)
            if newDirPath == path:
                logDebug('addFilePath', 'paths are equivalent - keeping existing path [%s]', path)
                evalPaths.append(path)
                appendPath = False
            elif newDirPath.startswith(path):
                logDebug('addFilePath', 'path [%s] is a subdirectory of [%s] - keeping new path [%s]', newDirPath, path, newDirPath)
                evalPaths.append(newDirPath)
                appendPath = False
            else:
                logDebug('addFilePath', 'keeping existing path [%s]', newDirPath)
                evalPaths.append(path)

        # path is a new path - keep it
        if appendPath:
            logDebug('addFilePath', 'keeping new path [%s]', newDirPath)
            evalPaths.append(newDirPath)

        return evalPaths
