package eu.bodynodesdev.host;


import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.core.app.ActivityScenario;

import org.junit.Test;
import org.junit.runner.RunWith;

import eu.bodynodesdev.host.pages.MainActivity;

@RunWith(AndroidJUnit4.class)
public class TestAllActivities {

    @Test
    public void testMainActivity_launchesSuccessfully() {
        ActivityScenario.launch(MainActivity.class);
    }

}
