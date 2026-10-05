package com.synapse.config;

import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@EnableConfigurationProperties(SynapseProperties.class)
public class SynapseServiceConfig {
}
