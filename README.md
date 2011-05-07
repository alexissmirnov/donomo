Donomo is a pay-as-you-go elastic OCR system.

Users upload paper scans. Donomo converts them into a searcheable PDF and emails the user the download link.

The processing is done in parralel on many ec2 nodes. ec2 nodes are instanciated based on how many work there is to do. Once the job is done idle worker commit suicide.

