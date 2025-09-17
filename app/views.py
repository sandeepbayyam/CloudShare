from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import filters

from .models import Destination
from .serializers import DestinationSerializer


# Create your views here.
class DestinationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for performing CRUD operations on Destination.
    Provides list, create, retrieve, update, and delete endpoints.
    """
    serializer_class = DestinationSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = '__all__'

    def get_queryset(self):
        """
        Override the default queryset if query parameters are provided.
        Example: filter by cloud and product destinations/?cloud=gcp&product=gcs.
        """
        query_params = self.request.query_params.dict()
        valid_fields = {f.name for f in Destination._meta.get_fields()}

        filters_keys = {key: value for key, value in query_params.items() if key in valid_fields}
        if filters_keys:
            return Destination.objects.filter(**filters_keys)
        return Destination.objects.all()

    def hanlde_validation_error(self, detail, code=status.HTTP_400_BAD_REQUEST):
        return ValidationError(detail, code=code)

    def validate_data(self, data, partial=False):
        """
        Validate payload for creating or updating a destination.
        Ensures the selected product is valid for the selected cloud.
        Ensures auth JSON contains required fields.
        - For create(POST), all required fields must be validated.
        - For update(PUT), all required fields must be validated.
        - For update(PATCH) partial update, only validate required fields present in the payload.
        """
        cloud = data.get("cloud")
        product = data.get("product")
        region = data.get("region")
        auth = data.get("auth", {} if not partial else data.get("auth"))

        # Define valid products for each cloud
        valid_products = {
            "aws": ["s3", "snowflake", "databricks", "redshift", "sftp"],
            "gcp": ["gcs", "bigquery", "snowflake", "databricks"],
            "azure": ["blobStorage", "snowflake", "databricks"],
        }

        # Cloud Validation
        if not partial or "cloud" in data:
            if not cloud:
                raise self.hanlde_validation_error({"cloud": "Cloud is required."})
            if cloud not in valid_products:
                raise self.hanlde_validation_error({"cloud": f"Invalid cloud: {cloud}."})

        # Product Validation
        if not partial or "product" in data:
            if not product:
                raise self.hanlde_validation_error({"product": "Product is required."})
            if product not in valid_products[cloud]:
                raise self.hanlde_validation_error({"product": f"Product '{product}' is not valid for cloud '{cloud}'. "})
        # Region Validation
        if not partial or "region" in data:
            if not region:
                raise self.hanlde_validation_error({"region": "Region is required."})

        # --- Auth Validation ---
        if not partial or "auth" in data:
            if not isinstance(auth, dict):
                raise self.hanlde_validation_error({"auth": "Auth must be a JSON object."})

            required_keys = []
            auth_type = auth.get("type")

            # AWS S3
            if cloud == "aws" and product == "s3":
                if not auth_type:
                    raise self.hanlde_validation_error({"auth": "Auth 'type' is required for AWS S3."})
                elif auth_type and auth_type not in ["ASSUME_ROLE", "CONSUMER_ROLE", "ACCESS_KEY"]:
                    raise self.hanlde_validation_error(
                        {"auth": f"Invalid auth type '{auth_type}' for AWS S3.Supported auth types are ASSUME_ROLE, CONSUMER_ROLE, ACCESS_KEY."})

                if auth_type == "ASSUME_ROLE":
                    required_keys = ["arn"]
                elif auth_type == "CONSUMER_ROLE":
                    required_keys = ["arn", "consumerArn"]
                elif auth_type == "ACCESS_KEY":
                    required_keys = ["accessKey", "secretAccessKey"]

            # GCP GCS
            elif cloud == "gcp" and product == "gcs":
                if not auth_type:
                    raise self.hanlde_validation_error({"auth": "Auth 'type' is required for GCP GCS."})
                elif auth_type and auth_type not in ["EXTERNAL_ACCESS", "IMPERSONATION"]:
                    raise self.hanlde_validation_error(
                        {"auth": f"Invalid auth type '{auth_type}' for GCP GCS. Supported auth types are EXTERNAL_ACCESS, IMPERSONATION."})

                if auth_type == "EXTERNAL_ACCESS":
                    required_keys = []  # only type required
                elif auth_type == "IMPERSONATION":
                    required_keys = ["serviceAccountToImpersonate"]

            # Azure Blob Storage
            elif cloud == "azure" and product == "blobStorage":
                access_identifiers = auth.get("accessIdentifiers", None)
                if not access_identifiers or not isinstance(access_identifiers, dict):
                    raise self.hanlde_validation_error({"auth": "accessIdentifiers is required for Azure Blob Storage and must be a JSON object."})

                apps = access_identifiers.get("consumerManagedApplications", None)
                if not apps or not isinstance(apps, list):
                    raise self.hanlde_validation_error({"auth": "At least one application is required in consumerManagedApplications."})

                for app in apps:
                    if not isinstance(app, dict) or "applicationId" not in app:
                        raise self.hanlde_validation_error({"auth": "Each application must contain 'applicationId'."})

            # GCP BigQuery
            elif cloud == "gcp" and product == "bigquery":
                access_identifiers = auth.get("accessIdentifiers", None)
                if not access_identifiers or not isinstance(access_identifiers, list):
                    raise self.hanlde_validation_error({"auth": "accessIdentifiers is required for GCP BigQuery and must be a non-empty array of objects."})

                for idx, identifier in enumerate(access_identifiers):
                    if not isinstance(identifier, dict):
                        raise self.hanlde_validation_error({f"accessIdentifiers[{idx}]": "Each accessIdentifier must be an object."})

                    granted_email = identifier.get("grantedEmail")
                    principal_type = identifier.get("principalType")

                    if not granted_email:
                        raise self.hanlde_validation_error({f"accessIdentifiers[{idx}].grantedEmail": "grantedEmail is required."})

                    allowed_principal_types = ["user", "group", "serviceAccount"]
                    if not principal_type or principal_type not in allowed_principal_types:
                        raise self.hanlde_validation_error(
                            {f"accessIdentifiers[{idx}].principalType": f"Invalid principalType '{principal_type}'. Allowed: {', '.join(allowed_principal_types)}"}
                        )
            # Snowflake on any cloud [AWS, GCP, Azure]
            elif product == "snowflake" and cloud in ["aws", "gcp", "azure"]:
                access_identifiers = auth.get("accessIdentifiers")
                if not access_identifiers or not isinstance(access_identifiers, list):
                    raise self.hanlde_validation_error(
                        {"accessIdentifiers": "accessIdentifiers is required for snowflake and must be a non-empty array of objects."})

                for idx, identifier in enumerate(access_identifiers):
                    if not isinstance(identifier, dict):
                        raise self.hanlde_validation_error({f"accessIdentifiers[{idx}]": "Each accessIdentifier must be an object."})

                    org_name = identifier.get("organizationName")
                    account_name = identifier.get("accountName")

                    if not org_name:
                        raise self.hanlde_validation_error(
                            {f"accessIdentifiers[{idx}].organizationName": "organizationName is required"})

                    if not account_name:
                        raise self.hanlde_validation_error({
                            f"accessIdentifiers[{idx}].accountName": "accountName is required"
                        })

            # Databricks on any cloud [AWS, GCP, Azure]
            elif product == "databricks" and cloud in ["aws", "gcp", "azure"]:
                access_identifiers = auth.get("accessIdentifiers")
                if not access_identifiers or not isinstance(access_identifiers, list):
                    raise self.hanlde_validation_error(
                        {"accessIdentifiers": "accessIdentifiers is required for Databricks and must be a non-empty array of objects."}
                    )

                for idx, identifier in enumerate(access_identifiers):
                    if not isinstance(identifier, dict):
                        raise self.hanlde_validation_error({f"accessIdentifiers[{idx}]": "Each accessIdentifier must be an object."})

                    metastore_id = identifier.get("metastoreId")

                    if not metastore_id:
                        raise self.hanlde_validation_error(
                            {f"accessIdentifiers[{idx}].metastoreId": "metastoreId is required"}
                        )
            # Amazon Redshift (AWS)
            elif cloud == "aws" and product == "redshift":
                accounts = auth.get("accounts")
                if not accounts or not isinstance(accounts, list):
                    raise self.hanlde_validation_error({"accounts": "accounts is required for Redshift and must be a non-empty array of objects."})

                for idx, account in enumerate(accounts):
                    if not isinstance(account, dict):
                        raise self.hanlde_validation_error({f"accounts[{idx}]": "Each account must be an object."})

                    account_id = account.get("accountId")

                    if not account_id:
                        raise self.hanlde_validation_error({f"accounts[{idx}].accountId": "accountId is required and must be a non-empty string."})

            # SFTP on AWS
            elif product == "sftp" and cloud == "aws":
                access_identifiers = auth.get("accessIdentifiers")
                if not access_identifiers or not isinstance(access_identifiers, list):
                    raise self.hanlde_validation_error(
                        {"accessIdentifiers": "accessIdentifiers is required for SFTP and must be a non-empty array of objects."}
                    )

                for idx, identifier in enumerate(access_identifiers):
                    if not isinstance(identifier, dict):
                        raise self.hanlde_validation_error({f"accessIdentifiers[{idx}]": "Each accessIdentifier must be an object."})

                    label = identifier.get("label")
                    public_key = identifier.get("publicKey")

                    if not label:
                        raise self.hanlde_validation_error(
                            {f"accessIdentifiers[{idx}].label": "label is required"}
                        )

                    if not public_key:
                        raise self.hanlde_validation_error(
                            {f"accessIdentifiers[{idx}].publicKey": "publicKey is required"}
                        )

            # Missing Key Check
            missing = [key for key in required_keys if key not in auth]
            if missing:
                raise self.hanlde_validation_error({"auth": f"Missing required keys for {cloud} {product} auth type '{auth_type}': {', '.join(missing)}"})

        return data

    def create(self, request, *args, **kwargs):
        """
        Create a new destination.
        url: /destinations/
        payload: { ...destination fields... }
        response: Created destination object
        """
        try:
            payload = self.validate_data(request.data)
            serializer = self.get_serializer(data=payload)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            status_code = getattr(e, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({"error": "Failed to create destination", "details": str(e)}, status=status_code)

    def update(self, request, *args, **kwargs):
        """
        Update an existing destination.
        url: /destinations/{id}/
        payload: { ...fields to update...}
        response: Updated destination object
        """
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            payload = self.validate_data(request.data, partial=partial)
            serializer = self.get_serializer(instance, data=payload, partial=partial)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            status_code = getattr(e, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({"error": "Failed to update destination", "details": str(e)}, status=status_code)

    def delete(self, request, *args, **kwargs):
        """
        Delete an existing destination.
        url: /destinations/{id}/
        payload: None
        path params: id (destination ID)
        query params: None
        response: Success message
        """
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({"message": "Destination deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            status_code = getattr(e, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({"error": "Failed to delete destination", "details": str(e)}, status=status_code)
