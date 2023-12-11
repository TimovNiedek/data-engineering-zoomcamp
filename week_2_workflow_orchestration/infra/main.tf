terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.8.0"
    }
  }
}

provider "google" {
  project     = var.project
  region      = var.region
  credentials = file(var.credentials)
}

resource "google_storage_bucket" "de_zoomcamp_bucket" {
  name          = var.gcs_bucket_name
  location      = var.location
  storage_class = var.gcs_storage_class
  force_destroy = false

  lifecycle_rule {
    condition {
      age = 14 # delete objects older than 3 days
    }
    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

resource "google_bigquery_dataset" "de_zoomcamp_dataset" {
  dataset_id                 = var.bq_dataset_name
  location                   = var.location
  delete_contents_on_destroy = true
}

resource "google_bigquery_table" "de_zoomcamp_table" {
  dataset_id = var.bq_dataset_name
  table_id   = var.bq_table_name
  deletion_protection = false

  schema = file(var.bq_table_schema)
}
