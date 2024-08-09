terraform {
  backend "s3" {
    bucket = "slack-app-terraform-state-bucket"
    key    = "environment-booking-app/terraform.tfstate"
    region = "us-west-2"
  }
}