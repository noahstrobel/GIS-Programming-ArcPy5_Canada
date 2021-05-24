# Name: Noah Strobel
#
# Class: GISc450
#
# Purpose: This script creates a new GDB (Strobel_Canada.gdb), clips
# shapefile data to the Canada boundary polygon, and then exports the
# clipped data to the new GDB. It prints the feature class (fc) names, type,
# and number of records. It then buffers the city fc to determine which are
# within 25 miles of a river and creates a new fc entitled "cities25."
# Additionally, it copies the city fc to a new fc entitled "CaCitiesRanked"
# and deletes CaCitiesRanked that are within 25 miles of a river.
# Finally, it joins the canadianCitiesPop CSV file to the CaCitiesRanked fc
# and deletes records that equal null.


import arcpy
import time
import os

arcpy.env.overwriteOutput = True

time_start = time.time()


def main():

    print("\nThis script creates a new GDB (Strobel_Canada.gdb),")
    print("clips shapefile data to the Canada boundary polygon,")
    print("and then exports that clipped data to the new GDB.")
    print("It prints the feature class (fc) names, type, and number")
    print("of records. It then creates a 25 mile buffer around the")
    print("city fc to determine which are within 25 miles of a river")
    print("and then creates a new fc entitled 'cities25.'")
    print("It then copies the city fc to a new fc entitled")
    print("'CaCitiesRanked' and deletes cities within 25 miles of a river.")
    print("Finally, it joins the canandianCitiesPop CSV file to the")
    print("CaCitiesRanked fc and deletes records that equal null")

    print("\n---Script starting---")

    # Creating the workspace and GDB location

    workspace = arcpy.env.workspace = r"C:\GISc450\ArcPy5_Canada"
    gdb_out = "Strobel_Canada.gdb"
    gdb_out_location = os.path.join(workspace, gdb_out)

    # Reading in the shapefiles

    cities_shp = r"C:\GISc450\ArcPy5_Canada\World\Cities.shp"
    country_shp = r"C:\GISc450\ArcPy5_Canada\World\Country.shp"
    lakes_shp = r"C:\GISc450\ArcPy5_Canada\World\Lakes.shp"
    rivers_shp = r"C:\GISc450\ArcPy5_Canada\World\Rivers.shp"
    city_pop_csv = r"C:\GISc450\ArcPy5_Canada\World\canadianCitiesPop.csv"

    # Creating the Strobel_Canada GDB

    arcpy.CreateFileGDB_management(workspace, gdb_out)

    if arcpy.Exists(gdb_out):
        print(f"\n{gdb_out} created in {workspace}")

    # Assigning the new GDB as our new workspace

    arcpy.env.workspace = gdb_out_location

    # Clipping the shapefiles to the Canada boundary

    country_name = arcpy.SelectLayerByAttribute_management(country_shp, "NEW_SELECTION", "CNTRY_NAME = 'Canada'")

    arcpy.Clip_analysis(cities_shp, country_name, "cities_canada")
    arcpy.Clip_analysis(country_shp, country_name, "canada_boundary")
    arcpy.Clip_analysis(lakes_shp, country_name, "lakes_canada")
    arcpy.Clip_analysis(rivers_shp, country_name, "rivers_canada")

    print(f"\nFeatures clipped to the Canada boundary")

    # Examining the shapefiles and printing their info

    fc_list = arcpy.ListFeatureClasses()

    print(f"\nFeatures extracted to {gdb_out}")
    print("")

    for fc in fc_list:
        desc = arcpy.Describe(fc)
        shape_type = desc.shapeType
        fc_name = desc.name
        get_count = arcpy.GetCount_management(fc)
        count = int(get_count.getOutput(0))

        print(f"{fc} is a {shape_type} feature containing {count} record(s)")

        # Projecting the newly-clipped shapefiles to the Canada_Lambert_Conformal_Conic projection

        reproject_name = fc_name + "_Project"
        new_projection = arcpy.SpatialReference(102002)
        arcpy.Project_management(fc, reproject_name, new_projection)
    print(f"\nFeature classes projected to {new_projection.name}")

    # Buffering the cities 25 miles

    arcpy.Buffer_analysis("cities_canada_Project", "cities_canada_Buffer", "25 miles")

    # Selecting the cities that are within 25 miles of a river

    cities_25mi = arcpy.SelectLayerByLocation_management("cities_canada_Project", "WITHIN_A_DISTANCE",
                                                         "rivers_canada_Project", "25 Miles")

    num_cities_25mi = arcpy.GetCount_management(cities_25mi)
    print(f"\n{num_cities_25mi} cities are within 25 miles of a river")

    cities_ranked = "CaCitiesRanked"
    cities25 = "cities25"

    # Creating our new cities25 and CaCitiesRanked feature classes and extracting them to the GDB

    arcpy.FeatureClassToFeatureClass_conversion(cities_25mi, gdb_out_location, "cities25")
    arcpy.FeatureClassToFeatureClass_conversion("cities_canada_Project", gdb_out_location, "CaCitiesRanked")
    print(f"\n{cities_ranked} and {cities25} created and extracted to GDB")

    # Selecting the cities not within 25 miles of a river

    cities_not_25mi = arcpy.SelectLayerByLocation_management("CaCitiesRanked", "WITHIN_A_DISTANCE",
                                                             "rivers_canada_Project", "25 Miles", "NEW_SELECTION",
                                                             "INVERT")
    num_cities_not_25mi = arcpy.GetCount_management(cities_not_25mi)

    # Selecting then deleting the CaCitiesRanked within 25 miles of a river

    within_25mi = arcpy.SelectLayerByLocation_management("CaCitiesRanked", "WITHIN_A_DISTANCE",
                                                         "rivers_canada_Project", "25 Miles", "NEW_SELECTION")
    arcpy.DeleteFeatures_management(within_25mi)

    print(f"\n{cities_ranked} within 25 miles of a river have been deleted")

    print(f"\nIncluding null records, {cities_ranked} contains {num_cities_not_25mi} records")

    # Joining the canadianCitiesPop CSV to the CaCitiesRanked feature class

    arcpy.JoinField_management("CaCitiesRanked", "OBJECTID", city_pop_csv, "Rank")

    # Selecting and then deleting the records in CaCitiesRanked that equal null

    cities_unranked = arcpy.SelectLayerByAttribute_management("CaCitiesRanked", "NEW_SELECTION",
                                                              "Rank IS NULL")
    arcpy.DeleteFeatures_management(cities_unranked)
    print(f"\nNull records have been deleted fom {cities_ranked}")

    # Counting the records in CaCitiesRanked after null records have been deleted

    ranked_num_records = arcpy.GetCount_management(cities_ranked)
    ranked_counter = int(ranked_num_records.getOutput(0))
    print(f"\n{cities_ranked} now contains {ranked_counter} records")


if __name__ == '__main__':
    main()

time_end = time.time()
total_time = time_end - time_start
minutes = int(total_time / 60)
seconds = total_time % 60
print(f"\n---The script finished in {minutes} minutes {int(seconds)} seconds---")
