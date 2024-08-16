terraform {
  backend "s3" {
    bucket                      = "slack-app-terraform-state-bucket"
    key                         = "environment-booking-app/terraform.tfstate"
    region                      = "us-west-2"
    endpoint                    = "http://localhost:4566"
    force_path_style            = true
    skip_credentials_validation = true
    skip_metadata_api_check     = true
  }
}