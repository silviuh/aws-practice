output "api_gateway_invoke_url" {
  value = "${aws_api_gateway_stage.api.invoke_url}/slack-command"
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.environments_table.name
}