package com.example.prophet_example_spring;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication(scanBasePackages = "com.example")
public class ProphetExampleSpringApplication {

	public static void main(String[] args) {
		SpringApplication.run(ProphetExampleSpringApplication.class, args);
	}

}
