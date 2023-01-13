# Live NCAAB betting data app

This repository contains all that is necessary to pull live sports betting data from ScoresAndOdds.com.  The app itself uses nothing outside of Deephaven's base installation to run.  It does, by default, install the [`sportsreference`](https://github.com/roclark/sportsipy) package for historical data.  It uses entirely Python to run, with the following three modules being the most critical to its usage:

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

## Usage

This repository has the same requirements to run as [deephaven-core](https://github.com/deephaven/deephaven-core). To run, from your shell:

```bash
./start.sh
```

Then, in your web browser (preferably Chrome or Firefox), navigate to `http://localhost:10000/ide/`.

## Notes

`scoresandodds.com` has changed since this app was written. The code has been updated to pull data for NCAAB games, but some of the fields are not populating properly. Fields include moneylines, home team record, and some spread risk metrics.

If you wish to see these corrected, reach out to me on [Slack](https://deephaven.io/slack).
