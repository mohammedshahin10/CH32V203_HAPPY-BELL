/*
 * FreeRTOSConfig.h -- HAPPY BELL / CH32V203G8R6
 *
 * Kernel source and the RISC-V/PFIC port under Firmware/FreeRTOS were
 * vendored from the user's own working "CH32V203-FreeRTOS" MounRiver
 * project (WCH's official kernel port for this chip family), unmodified.
 * This configuration file is project-specific and was written for HAPPY
 * BELL; it is NOT copied from that reference project except where noted.
 *
 * CH32V203G8R6 has only 20 KB SRAM (see AGENT.md / REQUIREMENTS.md). Every
 * value below was chosen to be conservative for that budget, not for
 * throughput. configTOTAL_HEAP_SIZE in particular MUST be re-checked
 * against the actual linker map once all application tasks/queues exist
 * (PENDING_TASKS.md) -- it is a starting point, not a measured value.
 */

#ifndef FREERTOS_CONFIG_H
#define FREERTOS_CONFIG_H
#include "debug.h"

/* See https://www.freertos.org/Using-FreeRTOS-on-RISC-V.html */

/* WCH CH32V20x has no RISC-V CLINT/MTIME; the PFIC SysTick + software
 * interrupt (SW_Handler) are used instead, per the vendored port. */
#define configMTIME_BASE_ADDRESS 	 ( 0 )
#define configMTIMECMP_BASE_ADDRESS  ( 0 )

#define configUSE_PREEMPTION			1
#define configUSE_IDLE_HOOK				0
#define configUSE_TICK_HOOK				0
#define configCPU_CLOCK_HZ				SystemCoreClock
#define configTICK_RATE_HZ				( ( TickType_t ) 1000 )
#define configMAX_PRIORITIES			( 8 )
#define configMINIMAL_STACK_SIZE		( ( unsigned short ) 128 )
#define configTOTAL_HEAP_SIZE			( ( size_t ) ( 6 * 1024 ) ) /* TBD: verify against link map */
#define configMAX_TASK_NAME_LEN			( 12 )
#define configUSE_TRACE_FACILITY		0
#define configUSE_16_BIT_TICKS			0
#define configIDLE_SHOULD_YIELD			1
#define configUSE_MUTEXES				1
#define configQUEUE_REGISTRY_SIZE		0
#define configCHECK_FOR_STACK_OVERFLOW	2
#define configUSE_RECURSIVE_MUTEXES		0
#define configUSE_MALLOC_FAILED_HOOK	1
#define configUSE_APPLICATION_TASK_TAG	0
#define configUSE_COUNTING_SEMAPHORES	1
#define configGENERATE_RUN_TIME_STATS	0
#define configUSE_PORT_OPTIMISED_TASK_SELECTION 0

/* Co-routines are unused; croutine.c is intentionally not built. */
#define configUSE_CO_ROUTINES 			0
#define configMAX_CO_ROUTINE_PRIORITIES ( 1 )

/* Archived RTOS configuration: software timers were never required. The
 * active NoneOS build implements periodic behavior in app_runtime.c. */
#define configUSE_TIMERS				0

/* Set the following definitions to 1 to include the API function, or zero
to exclude the API function. Trimmed to what the application actually uses
to save flash/RAM; add back as needed. */
#define INCLUDE_vTaskPrioritySet			0
#define INCLUDE_uxTaskPriorityGet			0
#define INCLUDE_vTaskDelete				0
#define INCLUDE_vTaskCleanUpResources		0
#define INCLUDE_vTaskSuspend				1
#define INCLUDE_vTaskDelayUntil				1
#define INCLUDE_vTaskDelay					1
#define INCLUDE_eTaskGetState				0
#define INCLUDE_xTimerPendFunctionCall		0
#define INCLUDE_xTaskAbortDelay				0
#define INCLUDE_xTaskGetHandle				0
#define INCLUDE_xSemaphoreGetMutexHolder	0

/* Normal assert() semantics without relying on the provision of an assert.h
header file. Halts with a visible serial message rather than failing
silently, per AGENT.md's "preserve visible error reporting" rule. */
#define configASSERT( x ) if( ( x ) == 0 ) { taskDISABLE_INTERRUPTS(); printf("FreeRTOS assert failed at %s:%d\r\n", __FILE__, __LINE__); while(1); }

/* Map to the platform printf function (USART1 debug helper). */
#define configPRINT_STRING( pcString )  printf( pcString )

#endif /* FREERTOS_CONFIG_H */
