variable "credentials" {
  description = "The credentials to use for GCP"
  type        = string
  default     = "./keys/datatalksclub-de-f023ee342729.json"
}

variable "project" {
  description = "The ID of the project in which to create resources"
  type        = string
  default     = "datatalksclub-de"
}

variable "region" {
  description = "The region in which to create resources"
  type        = string
  default     = "europe-west3"
}

variable "location" {
  description = "The location of the resources"
  type        = string
  default     = "EU"
}

variable "bq_dataset_name" {
  description = "The name of the BigQuery dataset to create"
  type        = string
  default     = "datatalksclub_de_demo_bq_dataset"
}

variable "gcs_bucket_name" {
  description = "The name of the GCS bucket to create"
  type        = string
  default     = "datatalksclub-de-demo-bucket"
}

variable "gcs_storage_class" {
  description = "The storage class of the GCS bucket"
  type        = string
  default     = "STANDARD"
}
