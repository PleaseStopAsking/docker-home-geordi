# Extended Personal Media Shows Agent

This metadata agent **needs to always be used with with the latest version** of the Extended Personal Media Scanner. See the instructions on this [page](https://bitbucket.org/mjarends/plex-scanners) for installing the scanner.

This is a Metadata Agent for personal media files. It works in conjunction with the Extended Personal Media Scanner to scan personal media shows. The meta data agent sets the summary details on the episode. The agent expects the files to follow the naming conventions for personal media that are outlined in the [Plex documentation](https://support.plex.tv/hc/en-us/sections/200068083-Naming-and-Organizing-Personal-Media).

## Change Log

[Change Log](https://forums.plex.tv/discussion/83440/rel-extended-personal-media-shows-agent/p1)

## Date-numbered shows

One major difference between the Extended Media Shows scanner and the Plex Series Scanner is that the Extended Media Shows scanner creates episode numbers for all of the date-based media.

This results in it being sorted correctly in all Plex user interfaces. The episode number is the day of the year in which the episode is dated plus the optional index value.

*If an index value is not specified then a one (01) is automatically appended to the end of the episode number.*

### Plex date-based naming standard

```plaintext
/Home Movies
   /Christmas
      /2010
         Christmas - 2010-01-06 - Getting Ready.m4v
         Christmas - 01-07-2010 - Getting Ready.m4v
         Christmas - 2010-12-24 - Stuffing_the_Stockings.m4v
         Christmas.12-25-2010.Christmas.Morning.m4v
```

### Season title in date-based shows

If you want to add a season title to your media then you will need to append it to the season number as shown in the example below. In addition to using a dash (-) as a separator, a period (.) or underscore (\_) can also be used.

```plaintext
/Home Movies
   /Christmas
      /2010 - Rocking around the tree
         2010-01-06 - Getting Ready.m4v
         12-24 - Stuffing the Stockings.m4v
```

The above example would result in the 2010 season having a title of **Rocking around the tree**.

### Unstructured format in date-based shows

Additionally the scanner and metadata agent also support unstructured content as well. What this means is that you could put all of your files in the same folder as long as the file name format looks like the following:

```plaintext
/Home Movies
   /Holidays
      /Christmas - 2011-12-25 - Getting Ready.m4v
      /Christmas - 2010-12-24 - Santa Claus.m4v
   /Birthdays
      /Grandma - 2010-02-24 - Grandma's 77th birthday party.m4v
      /Grandma - 2008-02-24 - Grandma's 75th birthday party.m4v
```

The above example would result in shows with **Christmas** and **Grandma** as the show titles. The season number, episode number and episode title would be parse from the names.

### Multiple episodes/shows on the same day

With this plug-in it is possible to have multiple shows on the same date.

An example of where this might be used in storing multiple NFL games in a directory with the same date. The Plex Series Scanner will see these as the same episode and will give them the same episode title.

The Extended Personal Media scanner and agent allow the user to specific an index number after the date to specify that the episode is different. This results in Plex showing the episode with the appropriate title.

```plaintext
/Sports
   /NFL
      /2013
         01-06_1 - Patriots Vs Giants.m4v
         01-06_2 - Houston Vs Minnesota.m4v
         2013-01-06_3 - Oakland Vs St. Lious.m4v
```

In the example of above three separate episode would be created in Plex and each with their own name.

## Date/time episodes

This section describes the formats that are supported for episodes that contain date and time in the episode file name and/or directory structure. Options that can be enabled for date/time episodes are covered in the [Plugin Configuration](#plugin-configuration) section below.

### Date/time formats supported

```plaintext
/Home Movies
   /Christmas
      /2010
         Christmas - 2010-01-06_01-03-43-AM - Getting Ready.m4v
         Christmas - 01.07.2010 05.15.15 - Getting Ready.m4v
         Christmas - 2010.12.24-11.23.23 AM - Stuffing_the_Stockings.m4v
         Christmas.12 25 2010_08 34 34.Christmas.Morning.m4v
   /Kids
      2015.01.23.12.34.34 AM - Playing outside
   /2010
      /12
         Christmas.12-25-2010_08.34.34.Christmas.Morning.m4v
   /2018
      /Christmas
         12.25.2018_08.34.34.Christmas.Morning.m4v
         12.25_08.34.34.Christmas.Morning.m4v
```

The following formats are supported for dates:

* YYYYMMDD
* YYYY[-|.| ]MM[-|.| ]DD
* MM[-|.| ]DD[-|.| ]YYYY

where:

* YYYY - is the 4-digit year
* MM - is the 2-digit month
* DD - is the 2-digit day of the month
* [-|.| ] - is the separator used between the date parts. Only one of the separator characters can be used.

The following formats are supported for time:

* HHMMSS[AM|PM]
* HHMM[AM|PM]
* HHMMSS
* HHMM
* HH[-|.| ]MM[-|.| ]SS[AM|PM]
* HH[-|.| ]MM[AM|PM]
* HH[-|.| ]M[-|.| ]MSS
* HH[-|.| ]MMSS
* HH[-|.| ]MM

where:

* HH - is 2-digit hours
* MM - is 2-digit minutes
* SS - is 2-digit seconds
* AM|PM - this needs to be specified if the time is not using 24 hour time. Only AM or PM may be specified.
* [-|.| ] - is the separator used between the date parts. Only one of the separator characters can be used.

The following characters can be used to separate the date and time in the episode file name:

* space ( )
* dash (-)
* period (.)
* underscore (_)

### Date and time format examples

The following shows an example of a date string for `January 1, 2001`:

* `2001-01-01`
* `01 01 2001`

The following shows an example of a time string for `1:05 PM`:

* `01 05 PM`
* `01.05.00 PM`
* `1305`

The following an example of a date and time string for `January 1, 2001 at 1:05 PM`:

* `2001-01-01_130500`
* `20010101 130500`
* `01012001-010500PM`

## Episode-number based shows

### Plex episode-based naming standard

```plaintext
/Home Movies
   /Christmas
      /2010
         Christmas - s2010e0106 - Getting Ready.m4v
         Christmas - s2010e0225 - Stuffing the Stockings.m4v
         Christmas - s2010e1225 - Christmas Morning.m4v
```

### Episodes that contain episode release dates

The following shows the different supported directory/file formats that are supported by the plug-in.

```plaintext
/Home Movies
    /NFL - s2015e01 - 2015-12-31 - Minnesota vs Green Bay.mp4
    /NFL - s2015e02 - 12-31-2015 - Detroit vs Tampa Bay.mp4
    /NFL
       /s2015e03 - 2015-12-31 - New England vs New York Jets.mp4
       /s2015e04 - 12-31-2015 - San Francisco vs Seattle.mp4
       /s2015
          /e05 - 2015-12-31 - Arizona vs Dallas.mp4
          /e06 - 12-31-2015 - New York Giants vs Philadelphia.mp4
       /e07 - 2015-12-31 - Cincinnati vs Pittsburgh.mp4
       /e08 - 12-31-2015 - Episode Title.mp4
```

The above example would result in a show with **NFL** as the show title. The season number, episode number, episode release date and episode title would be parsed from the names. The example shows 8 episodes specified above each would show up having the release date of 12-31-2015 in Plex.

### Season title in episode-number based shows

If you want to add a season title to your media then you will need to append it to the season number as shown in the example below. In addition to using a dash (-) as a separator, a period (.) or underscore (\_) can also be used.

```plaintext
/Home Movies
   /Christmas
      /2010 - Christmas in Minnesota
         s2010e01 - Getting Ready.m4v
         e02 - Another episode.m4v
      /2011 - Christmas in California
         s2010e01 - Getting Ready.m4v
```

The above example would result in the 2010 season having a title of **Christmas in Minnesota** and the 2011 season having a title of **Christmas in California**.

### Unstructured format in episode-number based shows

```plaintext
/Home Movies
   /Holidays
      /Christmas - s2010e01 - Getting Ready.m4v
   /Vacations
      /Italy - s2010e01 - Getting Ready.m4v
```

The above example would result in shows with **Christmas** and **Italy** as the show titles. The season number, episode number and episode title would be parsed from the names.

### Using Chapter or Lesson instead of Season

#### Chapter

Additionally the plugin supports using "Chapter" and "C" instead of "Season" and "S" (case is ignored).

**Note: the word "Season" would still be used in the Plex user interface and cannot be changed by the metadata agent plugin.**

```plaintext
/College Classes
   /Physics 101
      Physics 101 - c1e1 - First chapter.m4v
      Physics 101 - c1e2 - 2nd chapter.m4v
      /C2
         e1 - Some notes.m4v
         e2 - Some more notes.m4v
      /Chapter3
         e1 - Something else.m4v
         e2 - Something more.m4v
         e3 - Something real.m4v
```

The above example would result in 7 episodes being added under three seasons with a show name of "Physics 101".

#### Lesson

The plugin also supports using "Lesson" instead of "Chapter" or "Season".

```plaintext
/Video Training
   /Some Video Training
      /Lesson01
         01 - video1.m4v
         02 - video2.m4v
      /Lesson02
         01 - video1.m4v
         02 - video2.m4v
         03 - video3.m4v
```

## Summary Files

By default the plugin supports adding summaries to shows, seasons and episodes within Plex. To use this feature create `.summary` file following the directions from the secions below.

### Show summaries

Show summaries can be added to media files in Plex by creating a file with the show name and a ".summary" extension somewhere within the directory path of your media file that you want to add the summary to.

*It is important to note that the first file found will be used as the summary information for the show.*

There are two formats supported for show summary files:

* **[Show title].summary** where [Show title] is the name of your show that you want the summary information to be added to
* **show.summary**

Example media file:

`/Media Root/Show title/Show title - 2010-02-02 - Some title.mp4`

Summary file:

`/Media Root/Show title/Show title.summary`

### Season summaries

Season summaries can be added to media files in Plex by creating a file with the season name and a ".summary" extension somewhere within the directory path of your media file that you want to add the summary to.

*It is important to note that the first file found will be used as the summary information for the season.*

The following formats are supported for season summary files:

* **[Show title]-[S|s|C|c|L|l][Season Number].summary**
* **[season|chapter|lesson]-[Season Number].summary**
* **[S|s|C|c|L|l][Season Number].summary**

Where:

* **[Show title]** is the name of your show that you want the summary information to be added to
* **[S|s|C|c|L|l]** is abbreviation for season, chapter or lesson
* **[Season Number]** is the season number of the show

Example media file:

`/Media Root/Show title/Show title - 2010-02-02 - Some title.mp4`

Summary file:

`/Media Root/Show title/Show title-S2010.summary`

### Episode summaries

Episode summaries can be added to media files in Plex by creating a file with the same name and a ".summary" extension in the same directory as the media file you want to add the summary to.

Example media file:

`Show title - 2010-02-02 - Some title.mp4`

Summary file:

`Show title - 2010-02-02 - Some title.summary`

## Metadata Files

The plugin additionally supports using metadata files for shows and episodes within Plex. To use this feature you will need to enable the options within the plugin's settings in Plex and then create a `.metadata` file following the directions from the secions below.

### Show metadata

Metadata can be added to a show in Plex by creating a metadata file in the root directory of your show.

See the next sections for details on creating and naming show metadata files.

#### Show metadata file data and format

The following values can be set on a show from a metadata file:

| Attribute Name | Description | Format |
| -------------- | ----------- | ------ |
| title | Title of the show | |
| summary | Summary of the show | |
| release | Release date of the show | YYYY-MM-DD |
| actors | Name of the actors in the show | Comma separated list |
| studio | Name of the studio that produced the show | |
| genres | List of generes for this show | Comma separated list |
| collections | List of collections that this show belongs to | Comma separated list |

#### Show metadata file naming formats

**IMPORTANT: The first file found will be used as the metadata for the show.**

There are two naming formats supported for show metadata files:

* **[Show title].metadata** where [Show title] is the name of your show that you want the summary information to be added to
* **show.metadata**

#### Show metadata file examples

An example show metadata file can be found [here](./Samples/show.metadata).

The following are examples of show metadata files following the formats:

``` plaintext
# [Show title].metadata pattern
My Show.metadata

# show.metadata pattern
show.metadata
```

### Season metadata

Metadata can be added to a season in Plex by creating a metadata file in the in the directory path between the episode and the show folder. The metadata agent will search starting in the episode directory up to the root of the folder for the metadata file.

See the next sections for details on creating and naming season metadata files.

#### Season metadata file data and format

The following values can be set on a season from a metadata file:

| Attribute Name | Description | Format |
| -------------- | ----------- | ------ |
| title | Title of the show | |
| summary | Summary of the show | |

#### Season metadata file naming formats

**IMPORTANT: The first file found will be used as the metadata for the season.**

There are multiple naming formats supported for season metadata files:

* **[Show title]-[S|s|C|c|L|l][Season Number].metadata**
* **[season|chapter|lesson]-[Season Number].metadata**
* **[S|s|C|c|L|l][Season Number].metadata**

Where:

* **[Show title]** is the name of your show that the metadata applies to
* **[S|s|C|c|L|l]** is an abbreviation for season, chapter or lesson. Only one letter can be used.
* **[Season Number]** is the season number to apply the metadata to

#### Season metadata file examples

An example season metadata file can be found [here](./Samples/season.metadata).

The following are examples of season metadata files following the formats:

``` plaintext
# [Show title]-[S|s|C|c|L|l][Season Number].metadata pattern
My Show - S10.metadata

#[season|chapter|lesson]-[Season Number].metadata pattern
chapter-1.metadata

# [S|s|C|c|L|l][Season Number].metadata pattern
l01.metadata
```

### Episode metadata

Metadata can be added to an episode in Plex by creating a an episode-level metadata file in the same directory as your media.

See the next sections for details on creating and naming episode metadata files.

#### Episode metadata file data and format

The following values can be set on an episode from a metadata file:

| Attribute Name | Description | Format |
| -------------- | ----------- | ------ |
| title | Title of the episode | |
| summary | Episode summary | |
| release | Release date of the episode | YYYY-MM-DD |
| writers | List of writers of the show | Comma separated list |
| directors | List of directors of the show | Comma separated list |

#### Episode metadata file naming formats

**IMPORTANT: The first file found will be used as the metadata for the episode.**

There is one naming pattern supported for episode metadata files:

* **[Episode title].metadata** where [Episode title] is the name of your episode that you want the metadata to be added to

#### Episode metadata file examples

An example episode metadata file can be found [here](./Samples/episode.metadata).

The following is an example of how to name an episode metadata file based on the episode file name.

If the episode file name is:

`Show title - 2010-02-02 - Some title.mp4`

Then the metadata file name would be:

`Show title - 2010-02-02 - Some title.metadata`

## Plugin configuration

This section describes the different configuration options available within the Extended Personal Media metadata agent plugin.

### Enable debug logging

Enable this option if you want to see more log messages in the plugin's log file.

This is disabled by default.

### Use last modified timestamp for episodes

Enable this option if want the plugin to use the episode file's last modified timestamp when setting the release date in Plex.

This is enabled by default.

### Use created timestamp for episodes

Enable this option if want the plugin to use the episode file's created on timestamp when setting the release date in Plex.

This is disabled by default.

If "Use last modified timestamp for episodes?" is enabled this option will be ignored.

### Enable episode title scrubbing

Enable this option if want the plugin to scrub certain characters from the episode title when setting the title in Plex.

### Comma separated list of values to scrub from the episode title

List of values to scrub from episode titles. This is only used if "Enable episode title scrubbing?" is enabled.

By default the value is set to ".= ,-= ,_= ". The value must follow the format A=B,C=D. In this example A will be replaced by B in the episode title and C will be replaced by D.

### File extension to use for summary files

File extension to use for summary files. Summary files allow you to add a description to an episode in Plex.

By default the value is set to "summary". _**NOTE:** The value should not start with a period "."_

### Use metadata file for shows

Enable this option to use metadata files for shows.

This is disabled by default.

### Use metadata file for seasons

Enable this option to use metadata files for seasons.

This is disabled by default.

### Use metadata file for episodes

Enable this option to use metadata files for episodes.

This is disabled by default.

### File extension to use for metadata files

File extension to use for show metadata files. _**NOTE:** The value should not start with a period "."_

By default the value is set to "metadata".

### Use time stamp from the file name in the episode title

Enable this option if you want the timestamp from the episode to be pre-pended to the episode title in Plex.

This is disabled by default.

### Episode title time stamp format

_**NOTE:** This value is only applicable if the "Use time stamp from the file name in the episode title" option is enabled._

The format to use when pre-pending the episode time to the episode title. Select "AM/PM" to format the time in 12 hour time or "24 Hour" to format the time in 24 hour time.

By default the value is "24 Hour".

### Use date from the file name in the episode title

Enable this option if you want the date from the episode to be pre-pended to the episode title in Plex.

This is disabled by default.

### Episode title date format

**NOTE:** This value is only applicable if the "Use time stamp from the file name in the episode title" option is enabled._

The format to use when pre-pending the episode date to the episode title. The following options are available:

* YYYY-MM-DD
* YYYY/MM/DD
* MM-DD
* MM/DD

By default the value is "YYYY-MM-DD".

## Download and source

[Download](https://bitbucket.org/mjarends/extendedpersonalmedia-agent.bundle/get/master.zip)

[Source](https://bitbucket.org/mjarends/extendedpersonalmedia-agent.bundle/src)

## Installation

### Prequisites

1. Install the Extended Personal Media Scanner. Use the instructions [here](https://bitbucket.org/mjarends/plex-scanners/src/master/README.md).


### Instructions

See the [official Plex documentation](https://support.plex.tv/articles/201106098-how-do-i-find-the-plug-ins-folder/) for details on locating your plug-ins directory.

1. Unzip the downloaded ZIP file, this gives you a file/folder with the name ExtendedPersonalMedia-Agent.bundle-master. Rename the folder to ExtendedPersonalMedia-Agent.bundle
2. Follow the instructions in the Mac, Windows, or Linux sections below to locate the `Plug-ins` folder on your system and install the plug-in.
3. Restart Plex Media Server (this is optional)
**On Mac and Windows**: just quit and start again
**On Linux (Ubuntu)**: sudo service plexmediaserver restart
4. In the Plex/Web application go to **Settings > Server > Agents > Shows > Extended Personal Media Shows**.
*Ensure that the **Local Media Assets (TV) agent** is checked and showing in the list. The Local Media Assets is needed to add subtitle or metadata attributes from the files to your media.*
5. In Plex/Web (the media manager), create a new "TV Shows" section and select Extended Personal Media Shows from the Agent dropdown menu (under Advanced Options).

#### Mac specific instructions

* Move ExtendedPersonalMedia-Agent.bundle to `~/Library/Application Support/Plex Media Server/Plug-ins`.
  * The easiest way to find this folder is to use the Go to folder... option in the Go menu of the Finder.
  * ~ is your home folder. If you can't find your Library folder, have a look at [OS X Lion: Where did my Library go?](http://reviews.cnet.com/8301-13727_7-20082044-263/os-x-lion-where-did-my-library-go/)

#### Windows specific instructions

* Move ExtendedPersonalMedia-Agent.bundle to the Plug-ins folder.
* Open File Explorer and navigate to `C:\Users\<User Name>\AppData\Local\Plex Media Server\Plug-ins` (if you moved your Plex user data directory then go to `<Plex User Data Directory>\Plex Media Server\Plug-ins`)

#### Linux (Ubuntu) specific instructions

* Move ExtendedPersonalMedia-Agent.bundle to `/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-ins`

```shell
cd "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Plug-ins"

sudo chown -R plex:plex ExtendedPersonalMedia-Agent.bundle
```

* Copy the Series folder from the plex-scanners folder created above to `/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Scanners`

## Plug-in Logs Location

This section details the plug-in log file and location on the different operating systems. Please send this log file to me so that I can perform additional analysis.

Plug-in log file name: `com.arendshome.plex.agents.personalmedia.log`

See the [official Plex documentation](https://support.plex.tv/articles/201106148-channel-log-files/) for plug-in log locations.

## More Information

See this [post](https://forums.plex.tv/discussion/83440/rel-extended-personal-media-shows-agent/p1) in the Plex forums for the change log and the discussion thread on this metadata agent.
