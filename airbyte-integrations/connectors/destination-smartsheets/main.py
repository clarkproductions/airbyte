#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from destination_smartsheets import destinationSmartsheets

if __name__ == "__main__":
    destination = destinationSmartsheets()
    launch(destination, sys.argv[1:])
