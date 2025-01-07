# AWS-Data-Pipeline-for-Click-Activity-Analysis
Scheduled batch data pipeline to transform raw click logs and save structured data in a RDS instance.

I have created a S3 bucket that holds all my certifications with public access 'on' and access logging 'on'. Access points to these certificates are put on my resume. Whenever someone clicks on these links, a raw log is generated with data like ip-address, timestamp,browser used, certificate accessed in the bucket.

This batch data pipeline will extract useful data like timestamp, certificate accessed, ip_address and transform these into proper formats and put them in a MySQl - RDS instance.
