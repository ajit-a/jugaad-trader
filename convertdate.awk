BEGIN {
    daysofmonth["01"] = 0; daysofmonth["02"] = 31; daysofmonth["03"] = 59;
    daysofmonth["04"] = 90; daysofmonth["05"] = 120; daysofmonth["06"] = 151;
    daysofmonth["07"] = 181; daysofmonth["08"] = 212; daysofmonth["09"] = 243;
    daysofmonth["10"] = 273; daysofmonth["11"] = 304; daysofmonth["12"] = 334;
    fullday = 86400;
}
/[12][09][0-9][0-9][01][0-9][0123][0-9]/ {
    year = substr($0, 1, 4); month = substr($0, 5, 2); day = substr($0, 7, 2);
    date = ((year - 1970) * 365.25) + daysofmonth[month] + day - 1;
    if ((year % 4) == 0 && month > 2) { date = date + 1; }
    print date * fullday - (25200);
}
{}
