# output "api_gateway_invoke_url" {
#   value = "${aws_api_gateway_stage.api.invoke_url}/slack-command"
# }

# output "dynamodb_table_name" {
#   value = var.use_localstack ? module.localstack_resources[0].dynamodb_table_name : module.aws_resources[0].dynamodb_table_name
# }
#
# output "api_gateway_invoke_url" {
#   value = var.use_localstack ? module.localstack_resources[0].api_gateway_invoke_url : module.aws_resources[0].api_gateway_invoke_url
# }