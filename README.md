# Live NCAAB betting data app

This repository contains all that is necessary to pull live sports betting data from ScoresAndOdds.com.  The app itself uses nothing outside of Deephaven's base installation to run.  It uses entirely Python to run, with the following three modules being the most critical to its usage:

- `urllib`
- `re`
- `numpy`

## How it works

The app can be summarized in the following steps:

- Set the date you want to pull data for
  - To change the date, update the `date_of_games` variable.  Acceptable string format is `%Y-%m-%d`.
- Set the number of times you'd like to pull data
  - The default is 100.
- Set up the live table
- Pull data from ScoresAndOdds once every 15 seconds
  - This is more complex, as it parses the raw HTML from the page, and manages instances of missing data

## Current state

If you use Deephaven v0.9 or earlier, replace the line with `logRowPermissive` with `logRow`.  Otherwise, it should work as intended.

This app is functional, but in early development stages.  It will be updated and improved over time for a better user experience, cleaner code, and faster speeds.
