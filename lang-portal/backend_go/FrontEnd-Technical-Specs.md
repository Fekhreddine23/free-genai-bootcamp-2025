# Frontend Technical Spec

## Pages

### Dashboard '/dashboard'

#### Purpose

The purpose of this page is to provide a summary of learning
and act as the default page when the user visit the web app

This page contains the following components

#### Components

- Last study session

  - shows last activity used
  - shows when last activity used
  - summarizes wrong vs correct from last activity
  - has a link to the group

- Study Progress

  - total words study eg 3/124
    - across all study session show the total words studied out
      of all possible words in our database
  - Display a mastery progress eg. 0%

- Quick stats

  - sucess rate eg 80%
  - total study sessions eg. 4
  - total active group eg. 3
  - study streak eg. 4 days

- Start Studying Button
  - goes to study activity page

#### Need API Endpoints

We'll need following API endpoints to power this page

- GET api/dashboard/last_study_session
- GET api/dashboard/study_progress
- GET api/dashboard/quick-stats

### Study Activities Index '/study_activities'

#### Purpose

The purpose of this page is to show a collection of study activities
with a thumbnail and its name, to either lauch or view the study activity

#### Components

- study activity Card
  - show a thumbail of the study activity
  - The name of the study activity
  - a launch button to take us to the lauch page
  - the view page to view more informations about past study sessions
    for this study activity

#### Needed API Endpoints

- GET /api/study_activities

### Study Activity Show '/Study_activities/:id'

#### Purpose

The purpose of this page is to show the details of a study
activity ans its past study sessions.

#### Components

- Name of study activity
- Thumbnail of study activity
- Description of study activity
- Lauch button
- Study activities Paginate list.
  - Id
  - Activity Name
  - Group name
  - Start time
  - Number of review items

#### Need API Endpoints

- GET /api/study_activities/:id
- GET /api/study_activities/:id/study_sessions

### Study Activity Show '/Study_activities/:id/lauch'

#### Purpose

The purpose of this page is to lauch a study activity.

#### Components

- Name of study activity
- Lauch form
  - Select field for group
  - Launch now button

## Behaviour

After the form is submitted a new tabs open with the
study activity based on the URL provided in the database.

Also after form is submitted the page will redirect
to the study session show page.

#### Needed API Endpoints

- POST /api/study_activities

### Words Index '/words'

#### Purpose

The purpose is to show all words in our database

#### Components

- Pagined Word List
  - Columns
    - Japanese
    - Romaji
    - French
    - Correct Count
    - Wrong Count
  - Pagination with 100 items per page
  - Clicking the japanese word will take us to the word
  show page

#### Needed API Endpoints

- GET /api/words

### Word Show '/words/:id'

#### Purpose

The purpose of this page is to show information about
a specific word.

#### Components

- Japanese
- Romaji
- French
- Study statistics
  - Correct Count
  - Wrong Count
- Word Groups
  - Show an a series of pills eg. tags
  - When a group name is clicked it will
  take us to the group show page

#### Needed API Endpoints

- GET /api/words/:id


### Word Groups Index '/groups'

#### Purpose

The purpose of this page is to show a list of groups
in our database.


#### Components

- Paginated Group List
  - Columns
    - Groups Name
    - Word Count
  - Cliking the group name will take us to the group
  show page



#### Needed API Endpoints

- GET /api/groups

### Word Groups '/groups/:id'

#### Purpose

The purpose of this page is to show information
about a specific group.

#### Components

- Group Name
- Group Statistic
  - Total Word Count

- Words in Group ( Paginateds List of Words)
  - Should use the same component as the words index.

- Study session (Paginated List of Study Sessions)
  - Should use the same component as the study
  sessions index page.

#### Needed API Endpoints

- GET /api/groups/:id (the name and groups stats)
- GET /api/groups/:id/words
- GET /api/groups/:id/study_sessions


## Study Sessions Index '/Study_sessions'


#### Purpose

The purpose of this page is to show a list
of study sessions in our database.


#### Components

- Paginated Study Session List
  - Columns
    - ID
    - Activity Name
    - Group Name
    - Start Time
    - End Time
    - Number of Review Items

  - Cliking the study session id will take us to the
  study show page

#### Needed API Endpoints

- GET /api/study_sessions


### Study Session Show  '/Study_sessions/:id'

#### Purpose

The purpose of this page is to show information
about a specific study session.

#### Components

- Study Session Details
   - Activity Name
   - Group Name
   - Start Time
   - End Time
   - Number of Review Items
- Words Review Items (Paginated List of Words)
   - Should use the same component as the words index page


#### Needed API Endpoints

- GET /api/study_session/:id
- GET /api/study_sessions/:id/words

### Settings Page '/Settings'

#### Purpose

The purpose of this page is to make configurations to the study portal.

#### Components

- Theme Selection eg. Light, Dark, System Default
- Reset History Button
   -  this will delete all study session and word review items
- Full reset Button
   - This will drop all tables and re-create with seed data


#### Needed API Endpoints

- POST /api/reset_history
- POST /api/full_reset


#### Purpose
#### Components
#### Needed API Endpoints
