# docker run -v $(pwd)/src:/src \
#     -v $(pwd)/build:/build \
#     binxio/python-lambda-packager:3.7

aws cloudformation package \
    --template-file template.yml \
    --s3-bucket awschampionartifacts \
    --output-template-file packaged.yml

aws cloudformation validate-template \
    --template-body file://packaged.yml 

aws cloudformation deploy \
    --template-file packaged.yml \
    --capabilities CAPABILITY_IAM \
    --stack-name mytest
