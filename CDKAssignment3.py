from aws_cdk import ( # type: ignore
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_iam as iam,
    core
)

class NetworkStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create VPC
        self.vpc = ec2.Vpc(
            self, "MyVpc",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE,
                    name="Private",
                    cidr_mask=24
                )
            ]
        )

class ServerStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Web server security group
        web_server_sg = ec2.SecurityGroup(
            self, "WebServerSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for web servers"
        )
        web_server_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow inbound HTTP traffic"
        )

        # RDS security group
        rds_sg = ec2.SecurityGroup(
            self, "RDSSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for RDS"
        )
        rds_sg.add_ingress_rule(
            web_server_sg,
            ec2.Port.tcp(3306),
            "Allow inbound MySQL traffic from web servers"
        )

        # Launch web servers in public subnets
        for index, public_subnet in enumerate(vpc.public_subnets):
            instance = ec2.Instance(
                self, f"WebServer{index+1}",
                instance_type=ec2.InstanceType.of(
                    ec2.InstanceClass.BURSTABLE2,
                    ec2.InstanceSize.MICRO
                ),
                machine_image=ec2.AmazonLinuxImage(),
                vpc=vpc,
                vpc_subnets=ec2.SubnetSelection(subnets=[public_subnet]),
                security_group=web_server_sg
            )

        # Create RDS instance
        rds_instance = rds.DatabaseInstance(
            self, "MyRDSInstance",
            engine=rds.DatabaseInstanceEngine.mysql(
                version=rds.MysqlEngineVersion.VER_8_0
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE),
            security_groups=[rds_sg]
        )

app = core.App()

# Create network stack
network_stack = NetworkStack(app, "NetworkStack")

# Create server stack
server_stack = ServerStack(app, "ServerStack", vpc=network_stack.vpc)

app.synth()