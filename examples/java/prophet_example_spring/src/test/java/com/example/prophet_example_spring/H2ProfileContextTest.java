package com.example.prophet_example_spring;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.NONE)
@ActiveProfiles("h2")
class H2ProfileContextTest {

    @Test
    void contextLoadsWithH2Profile() {
    }
}
