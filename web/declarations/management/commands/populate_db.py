# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from declarations.models import Declaration, Resolution, OBJECTION, SUPPORT, SITUATION, NEUTRAL
from profiles.models import Profile, Speaker, State

import sys
import argparse
import json
#from django.utils import timezone
#from datetime import datetime
from dateutil.parser import parse

STATES = [
    ["AD", "AND", "020", "AN", "Andorra", "Andorra la Vella", 468.0, 84000, "EU"],
    ["AE", "ARE", "784", "AE", "United Arab Emirates", "Abu Dhabi", 82880.0, 4975593, "AS"],
    ["AF", "AFG", "004", "AF", "Afghanistan", "Kabul", 647500.0, 29121286, "AS"],
    ["AG", "ATG", "028", "AC", "Antigua and Barbuda", "St. John's", 443.0, 86754, "NA"],
    ["AI", "AIA", "660", "AV", "Anguilla", "The Valley", 102.0, 13254, "NA"],
    ["AL", "ALB", "008", "AL", "Albania", "Tirana", 28748.0, 2986952, "EU"],
    ["AM", "ARM", "051", "AM", "Armenia", "Yerevan", 29800.0, 2968000, "AS"],
    ["AN", "ANT", "530", "NT", "", "Willemstad", "960.0", 300000, "NA"],
    ["AO", "AGO", "024", "AO", "Angola", "Luanda", 1246700.0, 13068161, "AF"],
    ["AQ", "ATA", "010", "AY", "Antarctica", "", 14000000.0, 0, "AN"],
    ["AR", "ARG", "032", "AR", "Argentina", "Buenos Aires", 2766890.0, 41343201, "SA"],
    ["AS", "ASM", "016", "AQ", "American Samoa", "Pago Pago", 199.0, 57881, "OC"],
    ["AT", "AUT", "040", "AU", "Austria", "Vienna", 83858.0, 8205000, "EU"],
    ["AU", "AUS", "036", "AS", "Australia", "Canberra", 7686850.0, 21515754, "OC"],
    ["AW", "ABW", "533", "AA", "Aruba", "Oranjestad", 193.0, 71566, "NA"],
    ["AX", "ALA", "248", "", "Åland", "Mariehamn", 1580.0, 26711, "EU"],
    ["AZ", "AZE", "031", "AJ", "Azerbaijan", "Baku", 86600.0, 8303512, "AS"],
    ["BA", "BIH", "070", "BK", "Bosnia and Herzegovina", "Sarajevo", 51129.0, 4590000, "EU"],
    ["BB", "BRB", "052", "BB", "Barbados", "Bridgetown", 431.0, 285653, "NA"],
    ["BD", "BGD", "050", "BG", "Bangladesh", "Dhaka", 144000.0, 156118464, "AS"],
    ["BE", "BEL", "056", "BE", "Belgium", "Brussels", 30510.0, 10403000, "EU"],
    ["BF", "BFA", "854", "UV", "Burkina Faso", "Ouagadougou", 274200.0, 16241811, "AF"],
    ["BG", "BGR", "100", "BU", "Bulgaria", "Sofia", 110910.0, 7148785, "EU"],
    ["BH", "BHR", "048", "BA", "Bahrain", "Manama", 665.0, 738004, "AS"],
    ["BI", "BDI", "108", "BY", "Burundi", "Bujumbura", 27830.0, 9863117, "AF"],
    ["BJ", "BEN", "204", "BN", "Benin", "Porto-Novo", 112620.0, 9056010, "AF"],
    ["BL", "BLM", "652", "TB", "Saint Barthélemy", "Gustavia", 21.0, 8450, "NA"],
    ["BM", "BMU", "060", "BD", "Bermuda", "Hamilton", 53.0, 65365, "NA"],
    ["BN", "BRN", "096", "BX", "Brunei", "Bandar Seri Begawan", 5770.0, 395027, "AS"],
    ["BO", "BOL", "068", "BL", "Bolivia", "Sucre", 1098580.0, 9947418, "SA"],
    ["BQ", "BES", "535", "", "Bonaire", "", 328.0, 18012, "NA"],
    ["BR", "BRA", "076", "BR", "Brazil", "Brasilia", 8511965.0, 201103330, "SA"],
    ["BS", "BHS", "044", "BF", "Bahamas", "Nassau", 13940.0, 301790, "NA"],
    ["BT", "BTN", "064", "BT", "Bhutan", "Thimphu", 47000.0, 699847, "AS"],
    ["BV", "BVT", "074", "BV", "Bouvet Island", "", 49.0, 0, "AN"],
    ["BW", "BWA", "072", "BC", "Botswana", "Gaborone", 600370.0, 2029307, "AF"],
    ["BY", "BLR", "112", "BO", "Belarus", "Minsk", 207600.0, 9685000, "EU"],
    ["BZ", "BLZ", "084", "BH", "Belize", "Belmopan", 22966.0, 314522, "NA"],
    ["CA", "CAN", "124", "CA", "Canada", "Ottawa", 9984670.0, 33679000, "NA"],
    ["CC", "CCK", "166", "CK", "Cocos [Keeling] Islands", "West Island", 14.0, 628, "AS"],
    ["CD", "COD", "180", "CG", "Democratic Republic of the Congo", "Kinshasa", 2345410.0, 70916439, "AF"],
    ["CF", "CAF", "140", "CT", "Central African Republic", "Bangui", 622984.0, 4844927, "AF"],
    ["CG", "COG", "178", "CF", "Republic of the Congo", "Brazzaville", 342000.0, 3039126, "AF"],
    ["CH", "CHE", "756", "SZ", "Switzerland", "Bern", 41290.0, 7581000, "EU"],
    ["CI", "CIV", "384", "IV", "Ivory Coast", "Yamoussoukro", 322460.0, 21058798, "AF"],
    ["CK", "COK", "184", "CW", "Cook Islands", "Avarua", 240.0, 21388, "OC"],
    ["CL", "CHL", "152", "CI", "Chile", "Santiago", 756950.0, 16746491, "SA"],
    ["CM", "CMR", "120", "CM", "Cameroon", "Yaounde", 475440.0, 19294149, "AF"],
    ["CN", "CHN", "156", "CH", "China", "Beijing", 9596960.0, 1330044000, "AS"],
    ["CO", "COL", "170", "CO", "Colombia", "Bogota", 1138910.0, 47790000, "SA"],
    ["CR", "CRI", "188", "CS", "Costa Rica", "San Jose", 51100.0, 4516220, "NA"],
    ["CS", "SCG", "891", "YI", "", "Belgrade", 102350.0, 10829175, "EU"],
    ["CU", "CUB", "192", "CU", "Cuba", "Havana", 110860.0, 11423000, "NA"],
    ["CV", "CPV", "132", "CV", "Cape Verde", "Praia", 4033.0, 508659, "AF"],
    ["CW", "CUW", "531", "UC", "Curacao", "Willemstad", 444.0, 141766, "NA"],
    ["CX", "CXR", "162", "KT", "Christmas Island", "Flying Fish Cove", 135.0, 1500, "AS"],
    ["CY", "CYP", "196", "CY", "Cyprus", "Nicosia", 9250.0, 1102677, "EU"],
    ["CZ", "CZE", "203", "EZ", "Czech Republic", "Prague", 78866.0, 10476000, "EU"],
    ["DE", "DEU", "276", "GM", "Germany", "Berlin", 357021.0, 81802257, "EU"],
    ["DJ", "DJI", "262", "DJ", "Djibouti", "Djibouti", 23000.0, 740528, "AF"],
    ["DK", "DNK", "208", "DA", "Denmark", "Copenhagen", 43094.0, 5484000, "EU"],
    ["DM", "DMA", "212", "DO", "Dominica", "Roseau", 754.0, 72813, "NA"],
    ["DO", "DOM", "214", "DR", "Dominican Republic", "Santo Domingo", 48730.0, 9823821, "NA"],
    ["DZ", "DZA", "012", "AG", "Algeria", "Algiers", 2381740.0, 34586184, "AF"],
    ["EC", "ECU", "218", "EC", "Ecuador", "Quito", 283560.0, 14790608, "SA"],
    ["EE", "EST", "233", "EN", "Estonia", "Tallinn", 45226.0, 1291170, "EU"],
    ["EG", "EGY", "818", "EG", "Egypt", "Cairo", 1001450.0, 80471869, "AF"],
    ["EH", "ESH", "732", "WI", "Western Sahara", "El-Aaiun", 266000.0, 273008, "AF"],
    ["ER", "ERI", "232", "ER", "Eritrea", "Asmara", 121320.0, 5792984, "AF"],
    ["ES", "ESP", "724", "SP", "Spain", "Madrid", 504782.0, 46505963, "EU"],
    ["ET", "ETH", "231", "ET", "Ethiopia", "Addis Ababa", 1127127.0, 88013491, "AF"],
    ["FI", "FIN", "246", "FI", "Finland", "Helsinki", 337030.0, 5244000, "EU"],
    ["FJ", "FJI", "242", "FJ", "Fiji", "Suva", 18270.0, 875983, "OC"],
    ["FK", "FLK", "238", "FK", "Falkland Islands", "Stanley", 12173.0, 2638, "SA"],
    ["FM", "FSM", "583", "FM", "Micronesia", "Palikir", 702.0, 107708, "OC"],
    ["FO", "FRO", "234", "FO", "Faroe Islands", "Torshavn", 1399.0, 48228, "EU"],
    ["FR", "FRA", "250", "FR", "France", "Paris", 547030.0, 64768389, "EU"],
    ["GA", "GAB", "266", "GB", "Gabon", "Libreville", 267667.0, 1545255, "AF"],
    ["GB", "GBR", "826", "UK", "United Kingdom", "London", 244820.0, 62348447, "EU"],
    ["GD", "GRD", "308", "GJ", "Grenada", "St. George's", 344.0, 107818, "NA"],
    ["GE", "GEO", "268", "GG", "Georgia", "Tbilisi", 69700.0, 4630000, "AS"],
    ["GF", "GUF", "254", "FG", "French Guiana", "Cayenne", 91000.0, 195506, "SA"],
    ["GG", "GGY", "831", "GK", "Guernsey", "St Peter Port", 78.0, 65228, "EU"],
    ["GH", "GHA", "288", "GH", "Ghana", "Accra", 239460.0, 24339838, "AF"],
    ["GI", "GIB", "292", "GI", "Gibraltar", "Gibraltar", 6.5, 27884, "EU"],
    ["GL", "GRL", "304", "GL", "Greenland", "Nuuk", 2166086.0, 56375, "NA"],
    ["GM", "GMB", "270", "GA", "Gambia", "Banjul", 11300.0, 1593256, "AF"],
    ["GN", "GIN", "324", "GV", "Guinea", "Conakry", 245857.0, 10324025, "AF"],
    ["GP", "GLP", "312", "GP", "Guadeloupe", "Basse-Terre", 1780.0, 443000, "NA"],
    ["GQ", "GNQ", "226", "EK", "Equatorial Guinea", "Malabo", 28051.0, 1014999, "AF"],
    ["GR", "GRC", "300", "GR", "Greece", "Athens", 131940.0, 11000000, "EU"],
    ["GS", "SGS", "239", "SX", "South Georgia and the South Sandwich Islands", "Grytviken", 3903.0, 30, "AN"],
    ["GT", "GTM", "320", "GT", "Guatemala", "Guatemala City", 108890.0, 13550440, "NA"],
    ["GU", "GUM", "316", "GQ", "Guam", "Hagatna", 549.0, 159358, "OC"],
    ["GW", "GNB", "624", "PU", "Guinea-Bissau", "Bissau", 36120.0, 1565126, "AF"],
    ["GY", "GUY", "328", "GY", "Guyana", "Georgetown", 214970.0, 748486, "SA"],
    ["HK", "HKG", "344", "HK", "Hong Kong", "Hong Kong", 1092.0, 6898686, "AS"],
    ["HM", "HMD", "334", "HM", "Heard Island and McDonald Islands", "", 412.0, 0, "AN"],
    ["HN", "HND", "340", "HO", "Honduras", "Tegucigalpa", 112090.0, 7989415, "NA"],
    ["HR", "HRV", "191", "HR", "Croatia", "Zagreb", 56542.0, 4491000, "EU"],
    ["HT", "HTI", "332", "HA", "Haiti", "Port-au-Prince", 27750.0, 9648924, "NA"],
    ["HU", "HUN", "348", "HU", "Hungary", "Budapest", 93030.0, 9982000, "EU"],
    ["ID", "IDN", "360", "ID", "Indonesia", "Jakarta", 1919440.0, 242968342, "AS"],
    ["IE", "IRL", "372", "EI", "Ireland", "Dublin", 70280.0, 4622917, "EU"],
    ["IL", "ISR", "376", "IS", "Israel", "Jerusalem", 20770.0, 7353985, "AS"],
    ["IM", "IMN", "833", "IM", "Isle of Man", "Douglas", 572.0, 75049, "EU"],
    ["IN", "IND", "356", "IN", "India", "New Delhi", 3287590.0, 1173108018, "AS"],
    ["IO", "IOT", "086", "IO", "British Indian Ocean Territory", "Diego Garcia", 60.0, 4000, "AS"],
    ["IQ", "IRQ", "368", "IZ", "Iraq", "Baghdad", 437072.0, 29671605, "AS"],
    ["IR", "IRN", "364", "IR", "Iran", "Tehran", 1648000.0, 76923300, "AS"],
    ["IS", "ISL", "352", "IC", "Iceland", "Reykjavik", 103000.0, 308910, "EU"],
    ["IT", "ITA", "380", "IT", "Italy", "Rome", 301230.0, 60340328, "EU"],
    ["JE", "JEY", "832", "JE", "Jersey", "Saint Helier", 116.0, 90812, "EU"],
    ["JM", "JAM", "388", "JM", "Jamaica", "Kingston", 10991.0, 2847232, "NA"],
    ["JO", "JOR", "400", "JO", "Jordan", "Amman", 92300.0, 6407085, "AS"],
    ["JP", "JPN", "392", "JA", "Japan", "Tokyo", 377835.0, 127288000, "AS"],
    ["KE", "KEN", "404", "KE", "Kenya", "Nairobi", 582650.0, 40046566, "AF"],
    ["KG", "KGZ", "417", "KG", "Kyrgyzstan", "Bishkek", 198500.0, 5776500, "AS"],
    ["KH", "KHM", "116", "CB", "Cambodia", "Phnom Penh", 181040.0, 14453680, "AS"],
    ["KI", "KIR", "296", "KR", "Kiribati", "Tarawa", 811.0, 92533, "OC"],
    ["KM", "COM", "174", "CN", "Comoros", "Moroni", 2170.0, 773407, "AF"],
    ["KN", "KNA", "659", "SC", "Saint Kitts and Nevis", "Basseterre", 261.0, 51134, "NA"],
    ["KP", "PRK", "408", "KN", "North Korea", "Pyongyang", 120540.0, 22912177, "AS"],
    ["KR", "KOR", "410", "KS", "South Korea", "Seoul", 98480.0, 48422644, "AS"],
    ["KW", "KWT", "414", "KU", "Kuwait", "Kuwait City", 17820.0, 2789132, "AS"],
    ["KY", "CYM", "136", "CJ", "Cayman Islands", "George Town", 262.0, 44270, "NA"],
    ["KZ", "KAZ", "398", "KZ", "Kazakhstan", "Astana", 2717300.0, 15340000, "AS"],
    ["LA", "LAO", "418", "LA", "Laos", "Vientiane", 236800.0, 6368162, "AS"],
    ["LB", "LBN", "422", "LE", "Lebanon", "Beirut", 10400.0, 4125247, "AS"],
    ["LC", "LCA", "662", "ST", "Saint Lucia", "Castries", 616.0, 160922, "NA"],
    ["LI", "LIE", "438", "LS", "Liechtenstein", "Vaduz", 160.0, 35000, "EU"],
    ["LK", "LKA", "144", "CE", "Sri Lanka", "Colombo", 65610.0, 21513990, "AS"],
    ["LR", "LBR", "430", "LI", "Liberia", "Monrovia", 111370.0, 3685076, "AF"],
    ["LS", "LSO", "426", "LT", "Lesotho", "Maseru", 30355.0, 1919552, "AF"],
    ["LT", "LTU", "440", "LH", "Lithuania", "Vilnius", 65200.0, 2944459, "EU"],
    ["LU", "LUX", "442", "LU", "Luxembourg", "Luxembourg", 2586.0, 497538, "EU"],
    ["LV", "LVA", "428", "LG", "Latvia", "Riga", 64589.0, 2217969, "EU"],
    ["LY", "LBY", "434", "LY", "Libya", "Tripoli", 1759540.0, 6461454, "AF"],
    ["MA", "MAR", "504", "MO", "Morocco", "Rabat", 446550.0, 31627428, "AF"],
    ["MC", "MCO", "492", "MN", "Monaco", "Monaco", 1.9, 32965, "EU"],
    ["MD", "MDA", "498", "MD", "Republic of Moldova", "Chisinau", 33843.0, 4324000, "EU"],
    ["ME", "MNE", "499", "MJ", "Montenegro", "Podgorica", 14026.0, 666730, "EU"],
    ["MF", "MAF", "663", "RN", "Saint Martin", "Marigot", 53.0, 35925, "NA"],
    ["MG", "MDG", "450", "MA", "Madagascar", "Antananarivo", 587040.0, 21281844, "AF"],
    ["MH", "MHL", "584", "RM", "Marshall Islands", "Majuro", 181.3, 65859, "OC"],
    ["MK", "MKD", "807", "MK", "Macedonia", "Skopje", 25333.0, 2062294, "EU"],
    ["ML", "MLI", "466", "ML", "Mali", "Bamako", 1240000.0, 13796354, "AF"],
    ["MM", "MMR", "104", "BM", "Myanmar [Burma]", "Nay Pyi Taw", 678500.0, 53414374, "AS"],
    ["MN", "MNG", "496", "MG", "Mongolia", "Ulan Bator", 1565000.0, 3086918, "AS"],
    ["MO", "MAC", "446", "MC", "Macao", "Macao", 254.0, 449198, "AS"],
    ["MP", "MNP", "580", "CQ", "Northern Mariana Islands", "Saipan", 477.0, 53883, "OC"],
    ["MQ", "MTQ", "474", "MB", "Martinique", "Fort-de-France", 1100.0, 432900, "NA"],
    ["MR", "MRT", "478", "MR", "Mauritania", "Nouakchott", 1030700.0, 3205060, "AF"],
    ["MS", "MSR", "500", "MH", "Montserrat", "Plymouth", 102.0, 9341, "NA"],
    ["MT", "MLT", "470", "MT", "Malta", "Valletta", 316.0, 403000, "EU"],
    ["MU", "MUS", "480", "MP", "Mauritius", "Port Louis", 2040.0, 1294104, "AF"],
    ["MV", "MDV", "462", "MV", "Maldives", "Male", 300.0, 395650, "AS"],
    ["MW", "MWI", "454", "MI", "Malawi", "Lilongwe", 118480.0, 15447500, "AF"],
    ["MX", "MEX", "484", "MX", "Mexico", "Mexico City", 1972550.0, 112468855, "NA"],
    ["MY", "MYS", "458", "MY", "Malaysia", "Kuala Lumpur", 329750.0, 28274729, "AS"],
    ["MZ", "MOZ", "508", "MZ", "Mozambique", "Maputo", 801590.0, 22061451, "AF"],
    ["NA", "NAM", "516", "WA", "Namibia", "Windhoek", 825418.0, 2128471, "AF"],
    ["NC", "NCL", "540", "NC", "New Caledonia", "Noumea", 19060.0, 216494, "OC"],
    ["NE", "NER", "562", "NG", "Niger", "Niamey", 1267000.0, 15878271, "AF"],
    ["NF", "NFK", "574", "NF", "Norfolk Island", "Kingston", 34.6, 1828, "OC"],
    ["NG", "NGA", "566", "NI", "Nigeria", "Abuja", 923768.0, 154000000, "AF"],
    ["NI", "NIC", "558", "NU", "Nicaragua", "Managua", 129494.0, 5995928, "NA"],
    ["NL", "NLD", "528", "NL", "Netherlands", "Amsterdam", 41526.0, 16645000, "EU"],
    ["NO", "NOR", "578", "NO", "Norway", "Oslo", 324220.0, 5009150, "EU"],
    ["NP", "NPL", "524", "NP", "Nepal", "Kathmandu", 140800.0, 28951852, "AS"],
    ["NR", "NRU", "520", "NR", "Nauru", "Yaren", 21.0, 10065, "OC"],
    ["NU", "NIU", "570", "NE", "Niue", "Alofi", 260.0, 2166, "OC"],
    ["NZ", "NZL", "554", "NZ", "New Zealand", "Wellington", 268680.0, 4252277, "OC"],
    ["OM", "OMN", "512", "MU", "Oman", "Muscat", 212460.0, 2967717, "AS"],
    ["PA", "PAN", "591", "PM", "Panama", "Panama City", 78200.0, 3410676, "NA"],
    ["PE", "PER", "604", "PE", "Peru", "Lima", 1285220.0, 29907003, "SA"],
    ["PF", "PYF", "258", "FP", "French Polynesia", "Papeete", 4167.0, 270485, "OC"],
    ["PG", "PNG", "598", "PP", "Papua New Guinea", "Port Moresby", 462840.0, 6064515, "OC"],
    ["PH", "PHL", "608", "RP", "Philippines", "Manila", 300000.0, 99900177, "AS"],
    ["PK", "PAK", "586", "PK", "Pakistan", "Islamabad", 803940.0, 184404791, "AS"],
    ["PL", "POL", "616", "PL", "Poland", "Warsaw", 312685.0, 38500000, "EU"],
    ["PM", "SPM", "666", "SB", "Saint Pierre and Miquelon", "Saint-Pierre", 242.0, 7012, "NA"],
    ["PN", "PCN", "612", "PC", "Pitcairn Islands", "Adamstown", 47.0, 46, "OC"],
    ["PR", "PRI", "630", "RQ", "Puerto Rico", "San Juan", 9104.0, 3916632, "NA"],
    ["PS", "PSE", "275", "WE", "Palestine", "East Jerusalem", 5970.0, 3800000, "AS"],
    ["PT", "PRT", "620", "PO", "Portugal", "Lisbon", 92391.0, 10676000, "EU"],
    ["PW", "PLW", "585", "PS", "Palau", "Melekeok", 458.0, 19907, "OC"],
    ["PY", "PRY", "600", "PA", "Paraguay", "Asuncion", 406750.0, 6375830, "SA"],
    ["QA", "QAT", "634", "QA", "Qatar", "Doha", 11437.0, 840926, "AS"],
    ["RE", "REU", "638", "RE", "Réunion", "Saint-Denis", 2517.0, 776948, "AF"],
    ["RO", "ROU", "642", "RO", "Romania", "Bucharest", 237500.0, 21959278, "EU"],
    ["RS", "SRB", "688", "RI", "Serbia", "Belgrade", 88361.0, 7344847, "EU"],
    ["RU", "RUS", "643", "RS", "Russian Federation", "Moscow", 17100000.0, 140702000, "EU"],
    ["RW", "RWA", "646", "RW", "Rwanda", "Kigali", 26338.0, 11055976, "AF"],
    ["SA", "SAU", "682", "SA", "Saudi Arabia", "Riyadh", 1960582.0, 25731776, "AS"],
    ["SB", "SLB", "090", "BP", "Solomon Islands", "Honiara", 28450.0, 559198, "OC"],
    ["SC", "SYC", "690", "SE", "Seychelles", "Victoria", 455.0, 88340, "AF"],
    ["SD", "SDN", "729", "SU", "Sudan", "Khartoum", 1861484.0, 35000000, "AF"],
    ["SE", "SWE", "752", "SW", "Sweden", "Stockholm", 449964.0, 9828655, "EU"],
    ["SG", "SGP", "702", "SN", "Singapore", "Singapore", 692.7, 4701069, "AS"],
    ["SH", "SHN", "654", "SH", "Saint Helena", "Jamestown", 410.0, 7460, "AF"],
    ["SI", "SVN", "705", "SI", "Slovenia", "Ljubljana", 20273.0, 2007000, "EU"],
    ["SJ", "SJM", "744", "SV", "Svalbard and Jan Mayen", "Longyearbyen", 62049.0, 2550, "EU"],
    ["SK", "SVK", "703", "LO", "Slovakia", "Bratislava", 48845.0, 5455000, "EU"],
    ["SL", "SLE", "694", "SL", "Sierra Leone", "Freetown", 71740.0, 5245695, "AF"],
    ["SM", "SMR", "674", "SM", "San Marino", "San Marino", 61.2, 31477, "EU"],
    ["SN", "SEN", "686", "SG", "Senegal", "Dakar", 196190.0, 12323252, "AF"],
    ["SO", "SOM", "706", "SO", "Somalia", "Mogadishu", 637657.0, 10112453, "AF"],
    ["SR", "SUR", "740", "NS", "Suriname", "Paramaribo", 163270.0, 492829, "SA"],
    ["SS", "SSD", "728", "OD", "South Sudan", "Juba", 644329.0, 8260490, "AF"],
    ["ST", "STP", "678", "TP", "São Tomé and Príncipe", "Sao Tome", 1001.0, 175808, "AF"],
    ["SV", "SLV", "222", "ES", "El Salvador", "San Salvador", 21040.0, 6052064, "NA"],
    ["SX", "SXM", "534", "NN", "Sint Maarten", "Philipsburg", 21.0, 37429, "NA"],
    ["SY", "SYR", "760", "SY", "Syrian Arab Republic", "Damascus", 185180.0, 22198110, "AS"],
    #["SY", "SYR", "760", "SY", "Syria", "Damascus", 185180.0, 22198110, "AS"],
    ["SZ", "SWZ", "748", "WZ", "Swaziland", "Mbabane", 17363.0, 1354051, "AF"],
    ["TC", "TCA", "796", "TK", "Turks and Caicos Islands", "Cockburn Town", 430.0, 20556, "NA"],
    ["TD", "TCD", "148", "CD", "Chad", "N'Djamena", 1284000.0, 10543464, "AF"],
    ["TF", "ATF", "260", "FS", "French Southern Territories", "Port-aux-Francais", 7829.0, 140, "AN"],
    ["TG", "TGO", "768", "TO", "Togo", "Lome", 56785.0, 6587239, "AF"],
    ["TH", "THA", "764", "TH", "Thailand", "Bangkok", 514000.0, 67089500, "AS"],
    ["TJ", "TJK", "762", "TI", "Tajikistan", "Dushanbe", 143100.0, 7487489, "AS"],
    ["TK", "TKL", "772", "TL", "Tokelau", "", 10.0, 1466, "OC"],
    ["TL", "TLS", "626", "TT", "East Timor", "Dili", 15007.0, 1154625, "OC"],
    ["TM", "TKM", "795", "TX", "Turkmenistan", "Ashgabat", 488100.0, 4940916, "AS"],
    ["TN", "TUN", "788", "TS", "Tunisia", "Tunis", 163610.0, 10589025, "AF"],
    ["TO", "TON", "776", "TN", "Tonga", "Nuku'alofa", 748.0, 122580, "OC"],
    ["TR", "TUR", "792", "TU", "Turkey", "Ankara", 780580.0, 77804122, "AS"],
    ["TT", "TTO", "780", "TD", "Trinidad and Tobago", "Port of Spain", 5128.0, 1228691, "NA"],
    ["TV", "TUV", "798", "TV", "Tuvalu", "Funafuti", 26.0, 10472, "OC"],
    ["TW", "TWN", "158", "TW", "Taiwan", "Taipei", 35980.0, 22894384, "AS"],
    ["TZ", "TZA", "834", "TZ", "Tanzania", "Dodoma", 945087.0, 41892895, "AF"],
    ["UA", "UKR", "804", "UP", "Ukraine", "Kiev", 603700.0, 45415596, "EU"],
    ["UG", "UGA", "800", "UG", "Uganda", "Kampala", 236040.0, 33398682, "AF"],
    ["UM", "UMI", "581", "", "U.S. Minor Outlying Islands", "", 0.0, 0, "OC"],
    ["US", "USA", "840", "US", "United States of America", "Washington", 9629091.0, 310232863, "NA"],
    ["UY", "URY", "858", "UY", "Uruguay", "Montevideo", 176220.0, 3477000, "SA"],
    ["UZ", "UZB", "860", "UZ", "Uzbekistan", "Tashkent", 447400.0, 27865738, "AS"],
    ["VA", "VAT", "336", "VT", "Vatican City", "Vatican City", 0.4, 921, "EU"],
    ["VC", "VCT", "670", "VC", "Saint Vincent and the Grenadines", "Kingstown", 389.0, 104217, "NA"],
    ["VE", "VEN", "862", "VE", "Venezuela", "Caracas", 912050.0, 27223228, "SA"],
    ["VG", "VGB", "092", "VI", "British Virgin Islands", "Road Town", 153.0, 21730, "NA"],
    ["VI", "VIR", "850", "VQ", "U.S. Virgin Islands", "Charlotte Amalie", 352.0, 108708, "NA"],
    ["VN", "VNM", "704", "VM", "Vietnam", "Hanoi", 329560.0, 89571130, "AS"],
    ["VU", "VUT", "548", "NH", "Vanuatu", "Port Vila", 12200.0, 221552, "OC"],
    ["WF", "WLF", "876", "WF", "Wallis and Futuna", "Mata Utu", 274.0, 16025, "OC"],
    ["WS", "WSM", "882", "WS", "Samoa", "Apia", 2944.0, 192001, "OC"],
    ["XK", "XKX", "0  ", "KV", "Kosovo", "Pristina", 10908.0, 1800000, "EU"],
    ["YE", "YEM", "887", "YM", "Yemen", "Sanaa", 527970.0, 23495361, "AS"],
    ["YT", "MYT", "175", "MF", "Mayotte", "Mamoudzou", 374.0, 159042, "AF"],
    ["ZA", "ZAF", "710", "SF", "South Africa", "Pretoria", 1219912.0, 49000000, "AF"],
    ["ZM", "ZMB", "894", "ZA", "Zambia", "Lusaka", 752614.0, 13460305, "AF"],
    ["ZW", "ZWE", "716", "ZI", "Zimbabwe", "Harare", 390580.0, 13061000, "AF"],
]

class Command(BaseCommand):
    args = '<infile>'
    help = 'populate the database'

    def _create_state(self):
        pass

    def _create_declarations(self, infile):
        with open(infile) as f:
            pv = json.load(f)

            pv_header = pv['header']
            #date_creation = datetime.strptime(pv_header['meeting_date'].strip().replace('a.m.', 'AM').replace('p.m.', 'PM'), '%A, %d %B %Y, %I %p')
            print(pv_header['meeting_date'].strip())
            date_creation = parse(pv_header['meeting_date'].strip())

            for state in STATES:
                state = State(
                    iso_3166_alpha2=state[0],
                    iso_3166_alpha3=state[1],
                    iso_3166_numeric=state[2],
                    fips=state[3],
                    name=state[4],
                    capital=state[5],
                    area_in_km2=state[6],
                    population=state[7],
                    continent=state[8])
                state.save()

            for item in pv['items']:
                if 'header' not in item:
                    continue
                item_header = item['header']

                user = (Profile.objects.get(
                    username='admin'))

                resolution = Resolution(title=item_header['title'], user=user,
                    description=item_header['title'], is_featured=True,
                    date_creation=date_creation, is_published=True,
                    date_modification=date_creation,
                    is_public=True, language='en')
                resolution.save(skip_date_update=True)

                vote = {}
                for statement in item['statements']:
                    if 'vote' in statement:
                        vote = statement['vote']
                        #for state_name in vote['against']:
                        #  state = self._create_state()
                        #  resolution.in_favour.add(state)

                for statement in item['statements']:
                    # Check if state already exists
                    if 'speaker' in statement:
                        state_name = statement['speaker'].get('state', '')
                        if state_name:
                            state = (State
                                     .objects
                                     .filter(name=state_name)
                                     )
                            if not state.exists():
                                state = State(name=state_name)
                                state.save()
                            else:
                                state = state.first()
                        else:
                            state = None

                        # Check if speaker already exists
                        last_name = statement['speaker'].get('name', '')
                        speaker = (Speaker
                                   .objects
                                   .filter(last_name=last_name)
                                   )
                        if not speaker.exists():
                            speaker = Speaker(last_name=last_name, state=state)
                            speaker.save()
                        else:
                            speaker = speaker.first()

                        declaration_type = NEUTRAL
                        if vote and state_name:
                            if state_name in vote.get('in_favour', []):
                                declaration_type = SUPPORT
                            elif state_name in vote.get('against', []):
                                declaration_type = OBJECTION
                            elif state_name in vote.get('abstaining', []):
                                declaration_type = SITUATION

                        declaration = Declaration(resolution=resolution, speaker=speaker,
                            #text='\n\n'.join(statement.get('paragraphs', [])),
                            date_creation=date_creation,
                            text=' '.join(statement.get('paragraphs', [])),
                            is_approved=True, declaration_type=declaration_type)
                        declaration.save()

    def handle(self, infile, **kwargs):
        self._create_declarations(infile)
