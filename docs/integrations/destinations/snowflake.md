# Snowflake

Setting up the Snowflake destination connector involves setting up Snowflake entities (warehouse, database, schema, user, and role) in the Snowflake console, then setting up the data loading method (internal stage, AWS S3, GCS bucket, or Azure Blob Storage), and then configuring the Snowflake destination connector using the Airbyte UI.  

This page describes the step-by-step process of setting up the Snowflake destination connector.

## Prerequisites

- A Snowflake account with the[ ACCOUNTADMIN](https://docs.snowflake.com/en/user-guide/security-access-control-considerations.html) role. If you don’t have an account with the `ACCOUNTADMIN` role, contact your Snowflake administrator to set one up for you.
- (Optional) An AWS, Google Cloud Storage, or Azure account.

## Step 1: Set up Airbyte-specific entities in Snowflake

To set up the Snowflake destination connector, you first need to create Airbyte-specific Snowflake entities (a warehouse, database, schema, user, and role) with the `OWNERSHIP` permission to write data into Snowflake, track costs pertaining to Airbyte, and control permissions at a granular level.

You can use the following script in a new [Snowflake worksheet](https://docs.snowflake.com/en/user-guide/ui-worksheet.html) to create the entities:

1. [Log into your Snowflake account](https://www.snowflake.com/login/). 
2. Edit the following script to change the password to a more secure password and to change the names of other resources if you so desire.

    **Note:** Make sure you follow the [Snowflake identifier requirements](https://docs.snowflake.com/en/sql-reference/identifiers-syntax.html) while renaming the resources.
    
        -- set variables (these need to be uppercase)
        set airbyte_role = 'AIRBYTE_ROLE';
        set airbyte_username = 'AIRBYTE_USER';
        set airbyte_warehouse = 'AIRBYTE_WAREHOUSE';
        set airbyte_database = 'AIRBYTE_DATABASE';
        set airbyte_schema = 'AIRBYTE_SCHEMA';

        -- set user password
        set airbyte_password = 'password';

        begin;

        -- create Airbyte role
        use role securityadmin;
        create role if not exists identifier($airbyte_role);
        grant role identifier($airbyte_role) to role SYSADMIN;

        -- create Airbyte user
        create user if not exists identifier($airbyte_username)
        password = $airbyte_password
        default_role = $airbyte_role
        default_warehouse = $airbyte_warehouse;

        grant role identifier($airbyte_role) to user identifier($airbyte_username);

        -- change role to sysadmin for warehouse / database steps
        use role sysadmin;

        -- create Airbyte warehouse
        create warehouse if not exists identifier($airbyte_warehouse)
        warehouse_size = xsmall
        warehouse_type = standard
        auto_suspend = 60
        auto_resume = true
        initially_suspended = true;

        -- create Airbyte database
        create database if not exists identifier($airbyte_database);

        -- grant Airbyte warehouse access
        grant USAGE
        on warehouse identifier($airbyte_warehouse)
        to role identifier($airbyte_role);

        -- grant Airbyte database access
        grant OWNERSHIP
        on database identifier($airbyte_database)
        to role identifier($airbyte_role);

        commit;

        begin;

        USE DATABASE identifier($airbyte_database);

        -- create schema for Airbyte data
        CREATE SCHEMA IF NOT EXISTS identifier($airbyte_schema);

        commit;

        begin;

        -- grant Airbyte schema access
        grant OWNERSHIP
        on schema identifier($airbyte_schema)
        to role identifier($airbyte_role);

        commit;
        

3. Run the script using the [Worksheet page](https://docs.snowflake.com/en/user-guide/ui-worksheet.html) or [Snowlight](https://docs.snowflake.com/en/user-guide/ui-snowsight-gs.html). Make sure to select the **All Queries** checkbox.

## Step 2: Set up a data loading method

By default, Airbyte uses Snowflake’s [Internal Stage](https://docs.snowflake.com/en/user-guide/data-load-local-file-system-create-stage.html) to load data.

Make sure the database and schema have the `USAGE` privilege.

You can also store data externally using an [Amazon S3 bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html), a [Google Cloud Storage (GCS) bucket](https://cloud.google.com/storage/docs/introduction), or [Azure Blob Storage](https://docs.microsoft.com/en-us/azure/storage/blobs/).


### Using an Amazon S3 bucket

To use an Amazon S3 bucket, [create a new Amazon S3 bucket](https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html) with read/write access for Airbyte to stage data to Snowflake. 


### Using a Google Cloud Storage (GCS) bucket

To use a GCS bucket:

1. Navigate to the Google Cloud Console and [create a new GCS bucket](https://cloud.google.com/storage/docs/creating-buckets) with read/write access for Airbyte to stage data to Snowflake.
2. [Generate a JSON key](https://cloud.google.com/iam/docs/creating-managing-service-account-keys#creating_service_account_keys) for your service account. 
3. Edit the following script to replace `AIRBYTE_ROLE` with the role you used for Airbyte's Snowflake configuration and `YOURBUCKETNAME` with your GCS bucket name.
    ```text
    create storage INTEGRATION gcs_airbyte_integration
      TYPE = EXTERNAL_STAGE
      STORAGE_PROVIDER = GCS
      ENABLED = TRUE
      STORAGE_ALLOWED_LOCATIONS = ('gcs://YOURBUCKETNAME');

    create stage gcs_airbyte_stage
      url = 'gcs://YOURBUCKETNAME'
      storage_integration = gcs_airbyte_integration;

    GRANT USAGE ON integration gcs_airbyte_integration TO ROLE AIRBYTE_ROLE;
    GRANT USAGE ON stage gcs_airbyte_stage TO ROLE AIRBYTE_ROLE;

    DESC STORAGE INTEGRATION gcs_airbyte_integration;
    ```
    The final query should show a `STORAGE_GCP_SERVICE_ACCOUNT` property with an email as the property value. Add read/write permissions to your bucket with that email.
    
4. Navigate to the Snowflake UI and run the script as a [Snowflake account admin](https://docs.snowflake.com/en/user-guide/security-access-control-considerations.html) using the [Worksheet page](https://docs.snowflake.com/en/user-guide/ui-worksheet.html) or [Snowlight](https://docs.snowflake.com/en/user-guide/ui-snowsight-gs.html).

### Using Azure Blob Storage

To use Azure Blob Storage, you will need to [create a storage account](https://docs.microsoft.com/en-us/azure/storage/common/storage-account-create?tabs=azure-portal) and [container](https://docs.microsoft.com/en-us/rest/api/storageservices/create-container), and provide a [SAS Token](https://docs.snowflake.com/en/user-guide/data-load-azure-config.html#option-2-generating-a-sas-token) to access the container. We recommend creating a dedicated container for Airbyte to stage data to Snowflake. Airbyte needs read/write access to interact with this container.


## Step 3: Set up Snowflake as a destination in Airbyte

Navigate to the Airbyte UI to set up Snowflake as a destination. You'll need the following information to configure the Snowflake destination:

#### There are 2 way ways of oauth supported: login\pass and oauth2.

### Login and Password
| Field | Description |
|---|---|
| [Host](https://docs.snowflake.com/en/user-guide/admin-account-identifier.html) | The host domain of the snowflake instance (must include the account, region, cloud environment, and end with snowflakecomputing.com). Example: `accountname.us-east-2.aws.snowflakecomputing.com` |
| [Role](https://docs.snowflake.com/en/user-guide/security-access-control-overview.html#roles) | The role you created in Step 1 for Airbyte to access Snowflake. Example: `AIRBYTE_ROLE` |
| [Warehouse](https://docs.snowflake.com/en/user-guide/warehouses-overview.html#overview-of-warehouses) | The warehouse you created in Step 1 for Airbyte to sync data into. Example: `AIRBYTE_WAREHOUSE` |
| [Database](https://docs.snowflake.com/en/sql-reference/ddl-database.html#database-schema-share-ddl) | The database you created in Step 1 for Airbyte to sync data into. Example: `AIRBYTE_DATABASE` |
| [Schema](https://docs.snowflake.com/en/sql-reference/ddl-database.html#database-schema-share-ddl) | The default schema used as the target schema for all statements issued from the connection that do not explicitly specify a schema name.  |
| Username | The username you created in Step 1 to allow Airbyte to access the database. Example: `AIRBYTE_USER` |
| Password | The password associated with the username. |
| [JDBC URL Params](https://docs.snowflake.com/en/user-guide/jdbc-parameters.html) (Optional) | Additional properties to pass to the JDBC URL string when connecting to the database formatted as `key=value` pairs separated by the symbol `&`. Example: `key1=value1&key2=value2&key3=value3` |


### OAuth 2.0
Field | Description |
|---|---|
| [Host](https://docs.snowflake.com/en/user-guide/admin-account-identifier.html) | The host domain of the snowflake instance (must include the account, region, cloud environment, and end with snowflakecomputing.com). Example: `accountname.us-east-2.aws.snowflakecomputing.com` |
| [Role](https://docs.snowflake.com/en/user-guide/security-access-control-overview.html#roles) | The role you created in Step 1 for Airbyte to access Snowflake. Example: `AIRBYTE_ROLE` |
| [Warehouse](https://docs.snowflake.com/en/user-guide/warehouses-overview.html#overview-of-warehouses) | The warehouse you created in Step 1 for Airbyte to sync data into. Example: `AIRBYTE_WAREHOUSE` |
| [Database](https://docs.snowflake.com/en/sql-reference/ddl-database.html#database-schema-share-ddl) | The database you created in Step 1 for Airbyte to sync data into. Example: `AIRBYTE_DATABASE` |
| [Schema](https://docs.snowflake.com/en/sql-reference/ddl-database.html#database-schema-share-ddl) | The default schema used as the target schema for all statements issued from the connection that do not explicitly specify a schema name.  |
| Username | The username you created in Step 1 to allow Airbyte to access the database. Example: `AIRBYTE_USER` |
| OAuth2 | The Login name and password to obtain auth token. |
| [JDBC URL Params](https://docs.snowflake.com/en/user-guide/jdbc-parameters.html) (Optional) | Additional properties to pass to the JDBC URL string when connecting to the database formatted as `key=value` pairs separated by the symbol `&`. Example: `key1=value1&key2=value2&key3=value3` |


To use AWS S3 as the cloud storage, enter the information for the S3 bucket you created in Step 2:

| Field | Description |
|---|---|
| S3 Bucket Name | The name of the staging S3 bucket (Example: `airbyte.staging`). Airbyte will write files to this bucket and read them via statements on Snowflake.  |
| S3 Bucket Region | The S3 staging bucket region used. |
| S3 Key Id *  | The Access Key ID granting access to the S3 staging bucket. Airbyte requires Read and Write permissions for the bucket.  |
| S3 Access Key *  | The corresponding secret to the S3 Key ID. |
| Stream Part Size (Optional) | Increase this if syncing tables larger than 100GB. Files are streamed to S3 in parts. This determines the size of each part, in MBs. As S3 has a limit of 10,000 parts per file, part size affects the table size. This is 10MB by default, resulting in a default limit of 100GB tables. <br>Note, a larger part size will result in larger memory requirements. A rule of thumb is to multiply the part size by 10 to get the memory requirement. Modify this with care. (e.g. 5)  |
| Purge Staging Files and Tables | Determines whether to delete the staging files from S3 after completing the sync. Specifically, the connector will create CSV files named `bucketPath/namespace/streamName/syncDate_epochMillis_randomUuid.csv` containing three columns (`ab_id`, `data`, `emitted_at`). Normally these files are deleted after sync; if you want to keep them for other purposes, set `purge_staging_data` to false. |

To use GCS as the cloud storage, enter the information for the GCS bucket you created in Step 2:

| Field | Description |
|---|---|
| GCP Project ID | The name of the GCP project ID for your credentials. (Example: `my-project`)  |
| GCP Bucket Name | The name of the staging GCS bucket. Airbyte will write files to this bucket and read them via statements on Snowflake. (Example: `airbyte-staging`)  |
| Google Application Credentials | The contents of the JSON key file that has read/write permissions to the staging GCS bucket. You will separately need to grant bucket access to your Snowflake GCP service account. See the [GCP docs](https://cloud.google.com/iam/docs/creating-managing-service-account-keys#creating_service_account_keys) for more information on how to generate a JSON key for your service account.  |

To use Azure Blob storage, enter the information for the storage you created in Step 2:

| Field | Description |
|---|---|
| Endpoint Domain Name | Leave default value `blob.core.windows.net` or [map a custom domain](https://docs.microsoft.com/en-us/azure/storage/blobs/storage-custom-domain-name?tabs=azure-portal) to an Azure Blob Storage endpoint. |
| Azure Blob Storage Account Name | The Azure storage account you created in Step 2. |
| Azure blob storage container (Bucket) Name | The Azure blob storage container you created in Step 2. |
| SAS Token | The SAS Token you provided in Step 2. |


## Output schema 

Airbyte outputs each stream into its own table with the following columns in Snowflake:

| Airbyte field | Description | Column type |
|---|---|---|
| _airbyte_ab_id | A UUID assigned to each processed event | VARCHAR |
| _airbyte_emitted_at | A timestamp for when the event was pulled from the data source | TIMESTAMP WITH TIME ZONE |
| _airbyte_data | A JSON blob with the event data. | VARIANT |

**Note:** By default, Airbyte creates permanent tables. If you prefer transient tables, create a dedicated transient database for Airbyte. For more information, refer to[ Working with Temporary and Transient Tables](https://docs.snowflake.com/en/user-guide/tables-temp-transient.html)


## Supported sync modes

The Snowflake destination supports the following sync modes:

- [Full Refresh - Overwrite](https://docs.airbyte.com/understanding-airbyte/glossary#full-refresh-sync)
- [Full Refresh - Append](https://docs.airbyte.com/understanding-airbyte/connections/full-refresh-append)
- [Incremental Sync - Append](https://docs.airbyte.com/understanding-airbyte/connections/incremental-append)
- [Incremental Sync - Deduped History](https://docs.airbyte.com/understanding-airbyte/connections/incremental-deduped-history)

## Snowflake tutorials

Now that you have set up the Snowflake destination connector, check out the following Snowflake tutorials:

- [Build a data ingestion pipeline from Mailchimp to Snowflake](https://airbyte.com/tutorials/data-ingestion-pipeline-mailchimp-snowflake)
- [Replicate data from a PostgreSQL database to Snowflake](https://airbyte.com/tutorials/postgresql-database-to-snowflake)
- [Migrate your data from Redshift to Snowflake](https://airbyte.com/tutorials/redshift-to-snowflake)
- [Orchestrate ELT pipelines with Prefect, Airbyte and dbt](https://airbyte.com/tutorials/elt-pipeline-prefect-airbyte-dbt)


## Changelog

| Version | Date       | Pull Request | Subject |
|:--------|:-----------| :-----       | :------ |
| 0.4.24  | 2022-03-24 | [\#11093](https://github.com/airbytehq/airbyte/pull/11093) | Added OAuth support |
| 0.4.22  | 2022-03-18 | [\#10793](https://github.com/airbytehq/airbyte/pull/10793) | Fix namespace with invalid characters |
| 0.4.21  | 2022-03-18 | [\#11071](https://github.com/airbytehq/airbyte/pull/11071) | Switch to compressed on-disk buffering before staging to s3/internal stage |
| 0.4.20  | 2022-03-14 | [\#10341](https://github.com/airbytehq/airbyte/pull/10341) | Add Azure blob staging support |
| 0.4.19  | 2022-03-11 | [10699](https://github.com/airbytehq/airbyte/pull/10699) | Added unit tests                                                                   |
| 0.4.17  | 2022-02-25 | [10421](https://github.com/airbytehq/airbyte/pull/10421) | Refactor JDBC parameters handling                                                                   |
| 0.4.16  | 2022-02-25 | [\#10627](https://github.com/airbytehq/airbyte/pull/10627) | Add try catch to make sure all handlers are closed |
| 0.4.15  | 2022-02-22 | [\#10459](https://github.com/airbytehq/airbyte/pull/10459) | Add FailureTrackingAirbyteMessageConsumer |
| 0.4.14  | 2022-02-17 | [\#10394](https://github.com/airbytehq/airbyte/pull/10394) | Reduce memory footprint. |
| 0.4.13  | 2022-02-16 | [\#10212](https://github.com/airbytehq/airbyte/pull/10212) | Execute COPY command in parallel for S3 and GCS staging |
| 0.4.12  | 2022-02-15 | [\#10342](https://github.com/airbytehq/airbyte/pull/10342) | Use connection pool, and fix connection leak. |
| 0.4.11  | 2022-02-14 | [\#9920](https://github.com/airbytehq/airbyte/pull/9920) | Updated the size of staging files for S3 staging. Also, added closure of S3 writers to staging files when data has been written to an staging file. |
| 0.4.10  | 2022-02-14 | [\#10297](https://github.com/airbytehq/airbyte/pull/10297) | Halve the record buffer size to reduce memory consumption. |
| 0.4.9   | 2022-02-14 | [\#10256](https://github.com/airbytehq/airbyte/pull/10256) | Add `ExitOnOutOfMemoryError` JVM flag. |
| 0.4.8   | 2022-02-01 | [\#9959](https://github.com/airbytehq/airbyte/pull/9959) | Fix null pointer exception from buffered stream consumer. |
| 0.4.7   | 2022-01-29 | [\#9745](https://github.com/airbytehq/airbyte/pull/9745) | Integrate with Sentry. |
| 0.4.6   | 2022-01-28 | [#9623](https://github.com/airbytehq/airbyte/pull/9623) | Add jdbc_url_params support for optional JDBC parameters |
| 0.4.5   | 2021-12-29 | [#9184](https://github.com/airbytehq/airbyte/pull/9184) | Update connector fields title/description |
| 0.4.4   | 2022-01-24 | [#9743](https://github.com/airbytehq/airbyte/pull/9743) | Fixed bug with dashes in schema name |
| 0.4.3   | 2022-01-20 | [#9531](https://github.com/airbytehq/airbyte/pull/9531) | Start using new S3StreamCopier and expose the purgeStagingData option |
| 0.4.2   | 2022-01-10 | [#9141](https://github.com/airbytehq/airbyte/pull/9141) | Fixed duplicate rows on retries |
| 0.4.1   | 2021-01-06 | [#9311](https://github.com/airbytehq/airbyte/pull/9311) | Update сreating schema during check |
| 0.4.0   | 2021-12-27 | [#9063](https://github.com/airbytehq/airbyte/pull/9063) | Updated normalization to produce permanent tables |
| 0.3.24  | 2021-12-23 | [#8869](https://github.com/airbytehq/airbyte/pull/8869) | Changed staging approach to Byte-Buffered |
| 0.3.23  | 2021-12-22 | [#9039](https://github.com/airbytehq/airbyte/pull/9039) | Added part_size configuration in UI for S3 loading method |
| 0.3.22  | 2021-12-21 | [#9006](https://github.com/airbytehq/airbyte/pull/9006) | Updated jdbc schema naming to follow Snowflake Naming Conventions |
| 0.3.21  | 2021-12-15 | [#8781](https://github.com/airbytehq/airbyte/pull/8781) | Updated check method to verify permissions to create/drop stage for internal staging; compatibility fix for Java 17 |
| 0.3.20  | 2021-12-10 | [#8562](https://github.com/airbytehq/airbyte/pull/8562) | Moving classes around for better dependency management; compatibility fix for Java 17                               |
| 0.3.19  | 2021-12-06 | [#8528](https://github.com/airbytehq/airbyte/pull/8528) | Set Internal Staging as default choice                                                                              |
| 0.3.18  | 2021-11-26 | [#8253](https://github.com/airbytehq/airbyte/pull/8253) | Snowflake Internal Staging Support                                                                                  |
| 0.3.17  | 2021-11-08 | [#7719](https://github.com/airbytehq/airbyte/pull/7719) | Improve handling of wide rows by buffering records based on their byte size rather than their count                 |
| 0.3.15  | 2021-10-11 | [#6949](https://github.com/airbytehq/airbyte/pull/6949) | Each stream was split into files of 10,000 records each for copying using S3 or GCS                                 |
| 0.3.14  | 2021-09-08 | [#5924](https://github.com/airbytehq/airbyte/pull/5924) | Fixed AWS S3 Staging COPY is writing records from different table in the same raw table                             |
| 0.3.13  | 2021-09-01 | [#5784](https://github.com/airbytehq/airbyte/pull/5784) | Updated query timeout from 30 minutes to 3 hours                                                                    |
| 0.3.12  | 2021-07-30 | [#5125](https://github.com/airbytehq/airbyte/pull/5125) | Enable `additionalPropertities` in spec.json                                                                        |
| 0.3.11  | 2021-07-21 | [#3555](https://github.com/airbytehq/airbyte/pull/3555) | Partial Success in BufferedStreamConsumer                                                                           |
| 0.3.10  | 2021-07-12 | [#4713](https://github.com/airbytehq/airbyte/pull/4713)| Tag traffic with `airbyte` label to enable optimization opportunities from Snowflake                                |
